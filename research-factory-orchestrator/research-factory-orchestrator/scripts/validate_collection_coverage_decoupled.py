#!/usr/bin/env python3
"""Guard: collection coverage must be decoupled from work-unit completion.

Closes:
  * COVERAGE-DECOUPLE-MISSING — ``collection-coverage-result.passed`` derived
    from ``work_units_completed`` alone, not ``observed >= minimum``.
  * COLLECTION-COMPLETED-WITHOUT-SOURCES — ``collection_completed=true`` with
    ``observed_independent_sources < minimum`` while profile demands minimum.
  * STRICT-COVERAGE-UNREACHABLE — minimum > 0 but RFO_MAX_EXTERNAL_SOURCES cap
    < minimum (P0-1 in static audit).

stdlib-only, fail-closed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

VALIDATOR_ID = "validate_collection_coverage_decoupled"


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
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    cov = _load(rd / "collection-coverage-result.json")
    if not isinstance(cov, dict) or "_parse_error" in cov:
        issues.append({"code": "COVERAGE-RESULT-MISSING", "severity": "error", "detail": "collection-coverage-result.json missing or invalid"})
        _emit(False, True, issues, warnings, "no coverage result")
        return 1
    minimum = int(cov.get("minimum_independent_sources", 0) or 0)
    observed = int(cov.get("observed_independent_sources", 0) or 0)
    cov_passed = bool(cov.get("source_coverage_passed", False))
    completed = bool(cov.get("collection_completed", False))
    overall = bool(cov.get("passed", False))
    # 1. Threshold logic must be honest.
    if minimum > 0 and observed < minimum and cov_passed:
        issues.append({"code": "COVERAGE-DECOUPLE-MISSING", "severity": "error", "detail": f"observed={observed} < minimum={minimum} but source_coverage_passed=true"})
    if minimum == 0 and not cov_passed:
        issues.append({"code": "COVERAGE-DECOUPLE-INVERSION", "severity": "error", "detail": "minimum=0 should always pass coverage"})
    # 2. completed iff WUs terminal AND collector ran — must NOT imply coverage.
    if completed and minimum > 0 and observed < minimum and overall:
        issues.append({"code": "COLLECTION-COMPLETED-WITHOUT-SOURCES", "severity": "error", "detail": "collection_completed=true and overall passed but threshold not met"})
    # 3. Reachability: cap >= minimum.
    cap_env = os.environ.get("RFO_MAX_EXTERNAL_SOURCES")
    if cap_env and cap_env.isdigit() and minimum > int(cap_env):
        issues.append({"code": "STRICT-COVERAGE-UNREACHABLE", "severity": "error", "detail": f"RFO_MAX_EXTERNAL_SOURCES={cap_env} < minimum={minimum}"})
    # 4. Profile policy: if coverage.passed=false, gate must block downstream.
    if not overall:
        issues.append({"code": "COVERAGE-GATE-FAILED", "severity": "error", "detail": f"profile policy not satisfied: {cov.get('failure_reasons', [])}"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"coverage decoupling gate (min={minimum}, obs={observed})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
