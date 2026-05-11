#!/usr/bin/env python3
"""Shared SearXNG-style relay query params and light relevance ranking for RFO scripts."""
from __future__ import annotations

import os
import re
from typing import Any


def build_relay_params(query: str, num: int) -> dict[str, str]:
    """Defaults: safesearch=1 (or RFO_WEB_SEARCH_SAFESEARCH), engines from env or ``google``."""
    params: dict[str, str] = {"q": query, "format": "json", "num": str(num)}
    ss = os.environ.get("RFO_WEB_SEARCH_SAFESEARCH", "1").strip()
    if ss != "":
        params["safesearch"] = ss
    eng = os.environ.get("RFO_WEB_SEARCH_ENGINES", "").strip()
    if not eng:
        eng = os.environ.get("RFO_WEB_SEARCH_DEFAULT_ENGINES", "google").strip()
    if eng:
        params["engines"] = eng
    lang = os.environ.get("RFO_WEB_SEARCH_LANGUAGE", "").strip()
    if lang:
        params["language"] = lang
    return params


def relay_fetch_cap(requested_num: int) -> int:
    """Upper bound for SearXNG ``num`` must never be below ``requested_num`` (old default 20 starved fanout)."""
    requested_num = max(1, int(requested_num))
    raw = os.environ.get("RFO_WEB_SEARCH_FETCH_CAP", "").strip()
    if raw:
        try:
            return max(requested_num, int(raw))
        except ValueError:
            pass
    # Default: ask the relay for at least 2× what we keep (cap 200) so ranking/dedup has headroom.
    return max(requested_num, min(200, requested_num * 2))


def rank_relay_rows_for_task(task: str, rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Reorder relay rows by token overlap with task (Cyrillic/Latin tokens length >= 3)."""
    if not rows:
        return []
    raw_toks = re.findall(r"[\w\u0400-\u04FF]{3,}", (task or "").lower())
    toks = list(dict.fromkeys(raw_toks))[:16]
    if not toks:
        return rows[:limit]

    def score(r: dict[str, Any]) -> int:
        blob = (
            f"{r.get('title', '')} {r.get('snippet') or r.get('content', '')} {r.get('url', '')}"
        ).lower()
        return sum(1 for t in toks if t in blob)

    scored = sorted(rows, key=score, reverse=True)
    if os.environ.get("RFO_SEARCH_REL_REQUIRE_TOKEN_MATCH", "").strip() == "1":
        good = [r for r in scored if score(r) > 0]
        if len(good) >= min(limit, max(1, len(scored) // 2)):
            scored = good
    return scored[:limit]
