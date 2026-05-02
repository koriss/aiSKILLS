#!/usr/bin/env python3
"""Pre-execution intent alignment between handoff phases (SCF; arXiv:2604.16339)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_contract(name: str) -> dict:
    p = ROOT / "contracts" / "handoffs" / name
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    rd = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    d = rd / "handoffs"
    errs = []
    if not d.is_dir():
        print(json.dumps({"status": "fail", "message": "missing handoffs/"}, ensure_ascii=False))
        return 1
    for p in sorted(d.glob("HOFF-*.json")):
        o = json.loads(p.read_text(encoding="utf-8"))
        fp, tp = o.get("from_phase"), o.get("to_phase")
        key = f"{fp}-to-{tp}.json"
        c = load_contract(key)
        if not c:
            continue
        req = c.get("required_fields") or []
        payload = o.get("payload") or {}
        for f in req:
            if f not in payload:
                errs.append({"file": str(p), "missing_field": f, "contract": key})
    out = {"status": "fail" if errs else "pass", "errors": errs}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
