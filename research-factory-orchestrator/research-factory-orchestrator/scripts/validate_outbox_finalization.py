#!/usr/bin/env python3
"""Guard: ``run`` followed by ``validate`` BEFORE outbox finalization must FAIL.

Closes:
  * DIRECT-RUN-VALIDATE-FALSE-PASS — direct ``run`` then ``validate``
    historically passed because final-answer-gate.json existed without
    finalization. We require:
      - ``delivery-manifest.json`` ``delivery_status`` set,
      - ``final-answer-gate.json`` ``checks`` populated,
      - ``outbox-finalization.json`` (the explicit finalization breadcrumb)
        present and ``finalized=true``.
  * OUTBOX-FINALIZATION-WITHOUT-DELIVERY-MANIFEST — finalized=true but
    delivery-manifest.json missing or empty.

stdlib-only, fail-closed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_outbox_finalization"


def _emit(passed, blocking, issues, warnings, summary):
    print(json.dumps({"validator_id": VALIDATOR_ID, "schema_version": "v19.0", "passed": passed, "blocking": blocking, "issues": issues, "warnings": warnings, "summary": summary}, ensure_ascii=False))


def _load(p):
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_parse_error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--require-finalized", action="store_true", help="Treat missing finalization as blocking error (default: blocking).")
    ap.add_argument("--allow-pre-finalize", action="store_true", help="Allow run that has not been finalized (used by pre-outbox smokes).")
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues, warnings = [], []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    fag = _load(rd / "final-answer-gate.json")
    dm = _load(rd / "delivery-manifest.json")
    fin = _load(rd / "outbox-finalization.json")
    finalized = bool(isinstance(fin, dict) and fin.get("finalized"))
    if args.allow_pre_finalize:
        # Used by Phase 5 smokes: "direct run -> validate must FAIL pre-outbox".
        if finalized:
            issues.append({"code": "DIRECT-RUN-VALIDATE-FALSE-PASS", "severity": "error", "detail": "outbox-finalization.json claims finalized=true on a pre-outbox run"})
        if isinstance(dm, dict) and dm.get("delivery_status") in ("delivered", "stub_delivered", "partial_delivery", "failed", "validation_failed"):
            issues.append({"code": "DIRECT-RUN-VALIDATE-FALSE-PASS", "severity": "error", "detail": f"delivery_status={dm.get('delivery_status')!r} on a pre-outbox run"})
        blocking = any(i.get("severity") == "error" for i in issues)
        _emit(not blocking, blocking, issues, warnings, "pre-outbox guard")
        return 0 if not blocking else 1
    if not isinstance(fag, dict):
        issues.append({"code": "FAG-MISSING", "severity": "error", "detail": "final-answer-gate.json missing"})
    elif "checks" not in fag or not fag["checks"]:
        issues.append({"code": "FAG-CHECKS-EMPTY", "severity": "error", "detail": "final-answer-gate.json has no checks"})
    if not isinstance(dm, dict):
        issues.append({"code": "DELIVERY-MANIFEST-MISSING", "severity": "error", "detail": "delivery-manifest.json missing"})
    elif not dm.get("delivery_status"):
        issues.append({"code": "DELIVERY-MANIFEST-NO-STATUS", "severity": "error", "detail": "delivery-manifest.json has no delivery_status"})
    if not finalized:
        issues.append({"code": "OUTBOX-NOT-FINALIZED", "severity": "error", "detail": "outbox-finalization.json missing or finalized=false"})
    if finalized and not isinstance(dm, dict):
        issues.append({"code": "OUTBOX-FINALIZATION-WITHOUT-DELIVERY-MANIFEST", "severity": "error", "detail": "finalized=true but delivery-manifest.json missing"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"outbox finalization gate (finalized={finalized})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
