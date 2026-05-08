#!/usr/bin/env python3
"""Guard: runtime/errors.jsonl must be present and useful when failures occurred.

Closes a prior regression where ``.errors.log`` was 629 bytes for
10 RFO runs, hiding every meaningful failure (delivery stub_only, fetch errors,
validation failures). This guard scores the log along three dimensions:

  1. Present whenever the run produced any non-trivial failure surface
     (collection-result.backend in {no_results, no_seeds, no_network} OR
      delivery-manifest reports stub_only OR validation-transcript reports any
      failed validator).
  2. Each record carries ``code``, ``severity``, ``detail``, ``timestamp``.
  3. Code variety: at least one distinct code per failure surface that triggered.

stdlib-only, fail-closed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


VALIDATOR_ID = "validate_error_log_quality"
REQUIRED_FIELDS = ("code", "severity", "detail", "timestamp")


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": VALIDATOR_ID,
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": blocking,
                "issues": issues,
                "warnings": warnings,
                "summary": summary,
            },
            ensure_ascii=False,
        )
    )


def _load(p: Path):
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    log = rd / "runtime" / "errors.jsonl"
    cr = _load(rd / "collection-result.json") or {}
    dm = _load(rd / "delivery-manifest.json") or {}
    vt = _load(rd / "validation-transcript.json") or {}
    failure_surfaces: list[str] = []
    if cr.get("backend") in ("no_results", "no_seeds", "no_network"):
        failure_surfaces.append(f"collection_backend={cr['backend']}")
    if dm.get("delivery_status") in ("stub_only_no_external", "stub_delivered", "failed", "validation_failed", "partial_delivery"):
        failure_surfaces.append(f"delivery_status={dm['delivery_status']}")
    if isinstance(vt, dict) and vt.get("status") == "failed":
        failure_surfaces.append("validation_transcript=failed")
    expected_log = bool(failure_surfaces)
    records: list[dict] = []
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                issues.append({"code": "ERROR-LOG-INVALID-JSONL", "severity": "error", "detail": f"unparseable line: {line[:80]!r}"})
                continue
            if not isinstance(rec, dict):
                issues.append({"code": "ERROR-LOG-RECORD-NOT-OBJECT", "severity": "error", "detail": str(rec)[:80]})
                continue
            missing = [f for f in REQUIRED_FIELDS if f not in rec]
            if missing:
                issues.append({"code": "ERROR-LOG-RECORD-MISSING-FIELDS", "severity": "error", "detail": f"missing={missing}"})
            records.append(rec)
    if expected_log and not log.is_file():
        issues.append({"code": "ERROR-LOG-MISSING", "severity": "error", "detail": f"failure surfaces present but errors.jsonl missing: {failure_surfaces}"})
    elif expected_log and not records:
        issues.append({"code": "ERROR-LOG-EMPTY", "severity": "error", "detail": f"failure surfaces present but errors.jsonl is empty: {failure_surfaces}"})
    if records:
        codes = {r.get("code") for r in records if r.get("code")}
        if expected_log and len(codes) == 0:
            issues.append({"code": "ERROR-LOG-NO-CODES", "severity": "error", "detail": "no error codes present"})
        # Quality hint: at least one code per surface.
        if expected_log and len(codes) < len(failure_surfaces):
            warnings.append(
                {
                    "code": "ERROR-LOG-COVERAGE-THIN",
                    "severity": "warning",
                    "detail": f"distinct codes={sorted(codes)} surfaces={failure_surfaces}",
                }
            )
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"error-log gate (records={len(records)}, surfaces={failure_surfaces})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
