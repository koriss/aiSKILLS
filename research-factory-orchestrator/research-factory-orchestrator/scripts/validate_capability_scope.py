#!/usr/bin/env python3
"""Each OUT-* event should have a persisted capability token (OCap-style)."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    ob = rd / "outbox"
    if not ob.is_dir():
        print(json.dumps({"status": "pass", "note": "no outbox"}, ensure_ascii=False))
        return 0
    missing = []
    for jf in sorted(ob.glob("OUT-*.json")):
        ev = json.loads(jf.read_text(encoding="utf-8"))
        eid = str(ev.get("event_id") or jf.stem)
        cap = rd / "capability-tokens" / f"CAP-{eid}.json"
        if not cap.is_file():
            missing.append(eid)
    if missing:
        print(json.dumps({"status": "fail", "missing_capability_tokens": missing}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "pass", "events": len(list(ob.glob('OUT-*.json')))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
