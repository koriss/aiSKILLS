#!/usr/bin/env python3
"""Post-validation invariant: if validation-transcript failed, delivery artifacts must not claim success."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_no_delivery_after_validation_fail.py <run_dir>", file=sys.stderr)
        return 2
    rd = Path(sys.argv[1])
    vt = rd / "validation-transcript.json"
    if not vt.is_file():
        print(json.dumps({"status": "skip", "reason": "no validation-transcript.json"}, ensure_ascii=False))
        return 0
    tr = json.loads(vt.read_text(encoding="utf-8"))
    if tr.get("status") != "fail":
        return 0
    errs = []
    dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8")) if (rd / "delivery-manifest.json").is_file() else {}
    ds = str(dm.get("delivery_status") or "")
    if ds in ("delivered", "stub_delivered", "stub"):
        errs.append({"delivery_status_must_not_claim_sent": ds})
    fg = json.loads((rd / "final-answer-gate.json").read_text(encoding="utf-8")) if (rd / "final-answer-gate.json").is_file() else {}
    if fg.get("passed") is True:
        errs.append({"final_answer_gate_passed_must_be_false": True})
    st = json.loads((rd / "runtime-status.json").read_text(encoding="utf-8")) if (rd / "runtime-status.json").is_file() else {}
    if str(st.get("state") or "") != "validation_failed":
        errs.append({"runtime_state_expected_validation_failed": st.get("state")})
    if errs:
        print(json.dumps({"status": "fail", "errors": errs}, ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
