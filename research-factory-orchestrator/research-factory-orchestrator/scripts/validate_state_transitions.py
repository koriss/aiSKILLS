#!/usr/bin/env python3
"""Validate runtime state and inferred transition legality."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sm = json.loads((ROOT / "contracts" / "state-machine.json").read_text(encoding="utf-8"))
    valid = set(sm.get("states") or [])
    st_path = rd / "runtime-status.json"
    if not st_path.is_file():
        print(json.dumps({"status": "pass", "note": "no runtime-status"}, ensure_ascii=False))
        return 0
    st = json.loads(st_path.read_text(encoding="utf-8"))
    cur = str(st.get("state") or "")
    if cur not in valid:
        print(json.dumps({"status": "fail", "state": cur, "allowed": sorted(valid)}, ensure_ascii=False))
        return 1

    # Inferred transition sanity from artifacts/events.
    inferred_prev = "queued"
    if (rd / "trace.jsonl").is_file():
        body = (rd / "trace.jsonl").read_text(encoding="utf-8", errors="replace")
        if "runtime_completed" in body or "content_rendered" in body:
            inferred_prev = "content_rendered"
    if (rd / "outbox").is_dir():
        inferred_prev = "delivery_queued"

    if cur != inferred_prev:
        # Accept terminal states only if delivery acknowledgements exist.
        terminal = set(sm.get("terminal") or [])
        if cur in terminal and (rd / "delivery-acks").is_dir():
            print(json.dumps({"status": "pass", "state": cur, "inferred_prev": inferred_prev}, ensure_ascii=False))
            return 0
        print(json.dumps({"status": "fail", "state": cur, "inferred_prev": inferred_prev, "reason": "illegal_or_unproven_transition"}, ensure_ascii=False))
        return 1

    print(json.dumps({"status": "pass", "state": cur, "inferred_prev": inferred_prev}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
