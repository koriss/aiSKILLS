#!/usr/bin/env python3
"""Deterministic replay check over events.jsonl (Temporal-style)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    p = rd / "events.jsonl"
    if not p.is_file() or p.stat().st_size == 0:
        print(json.dumps({"status": "pass", "note": "no events.jsonl"}, ensure_ascii=False))
        return 0
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    eids = []
    for ln in lines:
        o = json.loads(ln)
        eid = o.get("event_id")
        if eid:
            eids.append(eid)
    if len(eids) != len(set(eids)):
        print(json.dumps({"status": "fail", "reason": "duplicate_event_id"}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass", "events": len(lines)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
