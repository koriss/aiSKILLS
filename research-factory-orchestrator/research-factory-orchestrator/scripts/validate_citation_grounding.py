#!/usr/bin/env python3
"""Guard: citation grounding result must exist and meet profile policy.

Closes:
  * CITATION-GROUNDING-MAGIC-LITERAL — outbox FAG had hardcoded 1.0 / 0.0
    instead of validator-derived RAF/DFL.
  * CITATION-GROUNDING-RESULT-MISSING — strict profile run with no result file.
  * CITATION-GROUNDING-RAF-BELOW-THRESHOLD / DFL-ABOVE-THRESHOLD — profile
    requires grounding but RAF/DFL fail.

stdlib-only, fail-closed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_citation_grounding"


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
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues, warnings = [], []
    cg = _load(rd / "citation-grounding-result.json")
    if not isinstance(cg, dict) or "_parse_error" in cg:
        issues.append({"code": "CITATION-GROUNDING-RESULT-MISSING", "severity": "error", "detail": "citation-grounding-result.json missing or invalid"})
        _emit(False, True, issues, warnings, "no citation-grounding result")
        return 1
    requires = bool(cg.get("requires_grounding", False))
    raf = float(cg.get("relevance_aware_factuality_score", 0.0) or 0.0)
    dfl = float(cg.get("deflection_rate_when_no_grounding", 0.0) or 0.0)
    raf_t = float(cg.get("raf_threshold", 0.65) or 0.65)
    dfl_t = float(cg.get("dfl_threshold", 0.25) or 0.25)
    grounded = int(cg.get("claims_grounded", 0) or 0)
    cg_passed = bool(cg.get("passed", False))
    if requires and raf < raf_t:
        issues.append({"code": "CITATION-GROUNDING-RAF-BELOW-THRESHOLD", "severity": "error", "detail": f"raf={raf} < {raf_t}"})
    if requires and dfl > dfl_t:
        issues.append({"code": "CITATION-GROUNDING-DFL-ABOVE-THRESHOLD", "severity": "error", "detail": f"dfl={dfl} > {dfl_t}"})
    if requires and grounded == 0:
        issues.append({"code": "CITATION-GROUNDING-NO-GROUNDED-CLAIMS", "severity": "error", "detail": "profile requires grounding; 0 grounded claims"})
    # Cross-check with FAG.
    fag = _load(rd / "final-answer-gate.json") or {}
    if isinstance(fag, dict):
        cgg = (fag.get("checks") or {}).get("citation_grounding_gate") if isinstance(fag.get("checks"), dict) else None
        if isinstance(cgg, dict):
            if cgg.get("validator_result_present") is False:
                warnings.append({"code": "FAG-CITATION-GROUNDING-WITHOUT-VALIDATOR", "severity": "warning", "detail": "FAG citation_grounding_gate marks validator_result_present=false despite present file"})
    if requires and not cg_passed and not issues:
        issues.append({"code": "CITATION-GROUNDING-OVERALL-FAILED", "severity": "error", "detail": str(cg.get("failure_reasons", []))})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"citation grounding gate (requires={requires}, raf={raf}, dfl={dfl})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
