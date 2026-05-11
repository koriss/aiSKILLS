#!/usr/bin/env python3
"""Multi-vector relay query fanout (deterministic templates + merge/dedup)."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib import parse as urllib_parse

_SKILL_ROOT = Path(__file__).resolve().parent.parent


def _config_path() -> Path:
    return _SKILL_ROOT / "contracts" / "query-fanout-config.json"


def load_fanout_config() -> dict[str, Any]:
    p = _config_path()
    if not p.is_file():
        return {"templates": ["{task}"], "default_max_templates": 4}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"templates": ["{task}"], "default_max_templates": 4}


def build_query_vectors(task: str, *, max_queries: int | None = None) -> list[str]:
    """Return unique non-empty query strings for relay fanout."""
    task = (task or "").strip()
    if not task:
        return []
    cfg = load_fanout_config()
    raw_templates = cfg.get("templates") if isinstance(cfg.get("templates"), list) else ["{task}"]
    cap = max_queries
    if cap is None:
        cap = int(cfg.get("default_max_templates") or 8)
    cap = max(1, min(cap, int(os.environ.get("RFO_QUERY_FANOUT_QUERIES", str(cap)) or cap)))
    seen: set[str] = set()
    out: list[str] = []
    for tpl in raw_templates:
        if len(out) >= cap:
            break
        if not isinstance(tpl, str):
            continue
        q = tpl.replace("{task}", task).strip()
        if not q or q in seen:
            continue
        seen.add(q)
        out.append(q)
    if not out:
        out = [task]
    return out[:cap]


def _url_norm(u: str) -> str:
    u = (u or "").strip()
    if not u.startswith("http"):
        return ""
    try:
        p = urllib_parse.urlparse(u)
        return urllib_parse.urlunparse(
            (p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", "", "", "")
        )
    except Exception:
        return u.split("#", 1)[0].strip()


def merge_relay_result_rows(rows_by_query: list[tuple[str, list[dict[str, Any]]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Dedupe by normalized URL; preserve first-seen row (title/snippet)."""
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_q: list[dict[str, Any]] = []
    total_in = 0
    for q, rows in rows_by_query:
        n = 0
        for r in rows:
            if not isinstance(r, dict):
                continue
            total_in += 1
            u = str(r.get("url") or "").strip()
            key = _url_norm(u)
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(dict(r))
            n += 1
        per_q.append({"query": q, "unique_added": n, "raw_rows": len(rows) if isinstance(rows, list) else 0})
    stats = {
        "queries_executed": len(per_q),
        "raw_rows_total": total_in,
        "unique_urls_after_dedup": len(merged),
        "per_query": per_q,
    }
    return merged, stats


def fanout_relay_search(
    query_fn,
    bases: list[str],
    task: str,
    per_query_num: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    query_fn(base, query, num) -> list[dict] relay rows.
    Respects RFO_RELAY_TOTAL_BUDGET_S (soft wall clock) and RFO_QUERY_FANOUT_QUERIES.
    """
    import time

    vectors = build_query_vectors(task)
    budget_s = float(os.environ.get("RFO_RELAY_TOTAL_BUDGET_S", "120") or "120")
    t0 = time.monotonic()
    rows_by_query: list[tuple[str, list[dict[str, Any]]]] = []
    relay_requests = 0
    for q in vectors:
        if time.monotonic() - t0 > budget_s:
            break
        got: list[dict[str, Any]] = []
        for base in bases:
            if time.monotonic() - t0 > budget_s:
                break
            relay_requests += 1
            got = query_fn(base, q, per_query_num)
            if got:
                break
        rows_by_query.append((q, got or []))
    merged, merge_stats = merge_relay_result_rows(rows_by_query)
    stats = {
        "query_vectors": vectors,
        "relay_requests": relay_requests,
        "merge": merge_stats,
        "budget_seconds": budget_s,
        "elapsed_seconds": round(time.monotonic() - t0, 3),
    }
    return merged, stats


def token_variants(task: str) -> list[str]:
    """Optional extra queries from long tasks (clauses)."""
    task = (task or "").strip()
    if len(task) < 40:
        return []
    parts = re.split(r"[.;]\s+", task)
    out: list[str] = []
    for p in parts[:3]:
        p = p.strip()
        if len(p) >= 12 and p not in out:
            out.append(p)
    return out
