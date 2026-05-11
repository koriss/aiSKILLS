#!/usr/bin/env python3
"""Shared SearXNG-style relay query params and light relevance ranking for RFO scripts."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
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


def body_text_signals_seed_garbage(text: str) -> bool:
    """
    Heuristic: relay fetch stored PDF bytes or raw HTML as "snippet" — not usable as claim body.

    Used by the relay bridge to avoid emitting claims from obvious binary/HTML dumps.
    """
    t = (text or "").lstrip()
    if not t:
        return False
    if t.startswith("%PDF"):
        return True
    head = t[:4000].lower()
    if "<!doctype html" in head or head.startswith("<html"):
        return True
    if head.count("<") > 40 and "skip to" in head and len(t) > 1500:
        return True
    return False


def _parse_searx_result_rows(data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw = data.get("results")
    if not isinstance(raw, list):
        return rows
    for r in raw[: max(1, int(limit))]:
        if not isinstance(r, dict):
            continue
        raw_url = str(r.get("url") or "").strip()
        if not raw_url.startswith("http"):
            continue
        rows.append(
            {
                "url": raw_url,
                "title": str(r.get("title", ""))[:300],
                "snippet": (str(r.get("content") or ""))[:500],
            }
        )
    return rows


def relay_json_search(
    api_base: str,
    query: str,
    fetch_num: int,
    *,
    user_agent: str,
    timeout: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Query a SearXNG-style ``/search`` endpoint for JSON ``results``.

    Many instances return **HTML** on ``GET …&format=json`` (UI page). In that case we
    retry with **POST** ``application/x-www-form-urlencoded`` (same fields), which matches
    common SearXNG operator configs.

    Returns ``(rows, meta)`` where ``meta`` describes transport and fallback reasons.
    """
    base = (api_base or "").strip().rstrip("/")
    meta: dict[str, Any] = {"transport": "get", "post_fallback": False, "api_base": base}
    if not base:
        return [], meta

    params = build_relay_params(query, max(1, int(fetch_num)))
    get_url = f"{base}/search?{urllib.parse.urlencode(params)}"

    def _try_parse_json(raw: bytes) -> dict[str, Any] | None:
        lead = raw.lstrip()[:2048]
        if lead.startswith(b"<") or lead.startswith(b"<!DOCTYPE") or lead.startswith(b"<html"):
            return None
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        return obj if isinstance(obj, dict) else None

    body = b""
    try:
        req = urllib.request.Request(get_url, headers={"User-Agent": user_agent, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read()
            meta["get_content_type"] = str(resp.headers.get("Content-Type") or "")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError, ValueError) as e:
        meta["get_error"] = str(e)[:240]

    data = _try_parse_json(body) if body else None
    if data is not None and isinstance(data.get("results"), list):
        meta["result_count"] = len(data.get("results") or [])
        return _parse_searx_result_rows(data, int(fetch_num)), meta

    meta["post_fallback"] = True
    meta["transport"] = "post"
    post_url = f"{base}/search"
    enc = urllib.parse.urlencode(params).encode("utf-8")
    post_req = urllib.request.Request(
        post_url,
        data=enc,
        method="POST",
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(post_req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read()
            meta["post_content_type"] = str(resp.headers.get("Content-Type") or "")
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError, ValueError) as e:
        meta["post_error"] = str(e)[:240]
        return [], meta

    data = _try_parse_json(body)
    if data is None:
        meta["post_parse_failed"] = True
        meta["body_preview"] = body[:160].decode("utf-8", errors="replace")
        return [], meta
    if not isinstance(data.get("results"), list):
        meta["post_no_results_key"] = True
        return [], meta
    meta["result_count"] = len(data.get("results") or [])
    return _parse_searx_result_rows(data, int(fetch_num)), meta


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
