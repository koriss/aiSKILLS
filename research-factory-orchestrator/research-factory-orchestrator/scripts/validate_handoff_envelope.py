#!/usr/bin/env python3
"""Validate handoffs/*.json envelopes (AgentAsk edge taxonomy: arXiv:2510.07593)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REQ = (
    "from_phase",
    "to_phase",
    "payload_hash",
    "required_fields",
    "success_response",
    "failure_response",
    "timeout_ms",
    "on_failure_action",
    "prev_hash",
    "handoff_id",
    "created_at",
)


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    d = rd / "handoffs"
    if not d.is_dir():
        print(json.dumps({"status": "fail", "message": "missing handoffs/ directory"}, ensure_ascii=False))
        return 1
    bad = []
    for p in sorted(d.glob("HOFF-*.json")):
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            bad.append({"file": str(p), "error": str(e)})
            continue
        miss = [k for k in REQ if k not in o]
        if miss:
            bad.append({"file": str(p), "missing": miss})
        if not isinstance(o.get("required_fields"), list):
            bad.append({"file": str(p), "error": "required_fields must be array"})
    out = {"status": "fail" if bad else "pass", "errors": bad, "checked": len(list(d.glob("HOFF-*.json")))}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
