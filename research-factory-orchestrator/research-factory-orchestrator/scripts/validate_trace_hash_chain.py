#!/usr/bin/env python3
"""Verify trace.jsonl hash chain end-to-end."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

GENESIS = "0" * 64


def _canon(rec: dict) -> str:
    d = {k: v for k, v in rec.items() if k != "record_hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    p = rd / "trace.jsonl"
    if not p.is_file():
        print(json.dumps({"status": "fail", "message": "missing trace.jsonl"}, ensure_ascii=False))
        return 1
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    prev_expected = GENESIS
    for i, ln in enumerate(lines):
        rec = json.loads(ln)
        if rec.get("prev_hash") != prev_expected:
            print(json.dumps({"status": "fail", "line": i, "expected_prev": prev_expected, "got": rec.get("prev_hash")}, ensure_ascii=False, indent=2))
            return 1
        rh = rec.get("record_hash")
        calc = hashlib.sha256(_canon(rec).encode("utf-8")).hexdigest()
        if rh != calc:
            print(json.dumps({"status": "fail", "line": i, "record_hash_mismatch": True}, ensure_ascii=False))
            return 1
        prev_expected = hashlib.sha256(ln.encode("utf-8")).hexdigest()
    print(json.dumps({"status": "pass", "lines": len(lines)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
