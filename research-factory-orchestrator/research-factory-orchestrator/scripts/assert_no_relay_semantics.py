#!/usr/bin/env python3
"""
Strict: scan machine JSON under ``--run-dir`` for **relay runtime** field names
(``web_search_json_api_base``, …). Does **not** flag ``web_search`` as a *collection_method* string.

Soft (optional): grep-ish scan of ``report/`` and ``chat/`` markdown/HTML for relay-hype phrases.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Keys that must not appear with a non-empty scalar in machine artifacts (relay wiring).
_RELAY_RUNTIME_KEYS = frozenset(
    {
        "web_search_json_api_base",
        "web_search_secondary_json_api_base",
    }
)

_SOFT_TEXT_PATTERNS = (
    re.compile(r"proof-of-fetch", re.I),
    re.compile(r"cryptographically\s+verified", re.I),
    re.compile(r"verified\s+retrieval", re.I),
)


def _walk(obj: object, path: str, hits: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k in _RELAY_RUNTIME_KEYS and v not in (None, "", [], {}):
                hits.append(f"relay_runtime_key:{p}={v!r}")
            _walk(v, p, hits)
    elif isinstance(obj, list):
        for i, it in enumerate(obj):
            _walk(it, f"{path}[{i}]", hits)


def _scan_json_files(run_dir: Path) -> list[str]:
    hits: list[str] = []
    for fp in sorted(run_dir.rglob("*.json")):
        rel = fp.relative_to(run_dir)
        if "node_modules" in rel.parts:
            continue
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        _walk(doc, str(rel), hits)
    return hits


def _soft_text_scan(run_dir: Path) -> list[str]:
    out: list[str] = []
    for sub in ("report", "chat"):
        d = run_dir / sub
        if not d.is_dir():
            continue
        for fp in sorted(d.rglob("*")):
            if fp.suffix.lower() not in (".md", ".html", ".htm"):
                continue
            text = fp.read_text(encoding="utf-8", errors="replace")
            if "agent-attested" in text.lower():
                continue
            for rx in _SOFT_TEXT_PATTERNS:
                if rx.search(text):
                    out.append(f"marketing_phrase:{fp.relative_to(run_dir)}:{rx.pattern}")
                    break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert no relay-runtime semantics in run-dir artifacts.")
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument(
        "--soft-text",
        action="store_true",
        help="Also warn on marketing phrases in report/chat without agent-attested disclaimer.",
    )
    args = ap.parse_args()
    rd = args.run_dir.expanduser().resolve(strict=False)
    if not rd.is_dir():
        print(json.dumps({"ok": False, "errors": [f"not_a_dir:{rd}"]}, indent=2))
        return 2

    strict = _scan_json_files(rd)
    soft = _soft_text_scan(rd) if args.soft_text else []

    if strict:
        print(json.dumps({"ok": False, "strict_errors": strict, "soft_warnings": soft}, indent=2))
        return 1
    if soft:
        print(json.dumps({"ok": True, "strict_errors": [], "soft_warnings": soft}, indent=2))
        return 0
    print(json.dumps({"ok": True, "strict_errors": [], "soft_warnings": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
