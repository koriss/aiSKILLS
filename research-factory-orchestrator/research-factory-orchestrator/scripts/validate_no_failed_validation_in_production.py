#!/usr/bin/env python3
"""Guard: contradictory production / validation / delivery claims (News Catalog class)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_no_failed_validation_in_production"


def _emit(passed: bool, issues: list) -> None:
    print(
        json.dumps(
            {
                "validator_id": VALIDATOR_ID,
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": not passed,
                "issues": issues,
                "warnings": [],
                "summary": "production claim hygiene",
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    run = {}
    if (rd / "run.json").is_file():
        try:
            run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        except Exception:
            run = {}
    mode = str(run.get("mode") or "").lower()
    fag = {}
    if (rd / "final-answer-gate.json").is_file():
        try:
            fag = json.loads((rd / "final-answer-gate.json").read_text(encoding="utf-8"))
        except Exception:
            fag = {}
    dm = {}
    if (rd / "delivery-manifest.json").is_file():
        try:
            dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8"))
        except Exception:
            dm = {}
    if isinstance(fag, dict):
        vs = str(fag.get("validation_status") or "").lower()
        pr = fag.get("production_ready")
        if vs == "failed" and pr is True:
            issues.append(
                {
                    "code": "PRODUCTION-CLAIM-MISMATCH-VALIDATION-FAILED",
                    "severity": "error",
                    "detail": "validation_status failed but production_ready true",
                }
            )
    if isinstance(dm, dict):
        ds = str(dm.get("delivery_status") or "").lower()
        red = dm.get("real_external_delivery")
        if ds == "delivered" and red is False:
            issues.append(
                {
                    "code": "PRODUCTION-CLAIM-MISMATCH-DELIVERY-STUB",
                    "severity": "error",
                    "detail": "delivery_status delivered but real_external_delivery false",
                }
            )
        if mode == "production" and ds == "stub_delivered":
            issues.append(
                {
                    "code": "PRODUCTION-CLAIM-MISMATCH-DELIVERY-STUB",
                    "severity": "error",
                    "detail": "stub_delivered under production mode",
                }
            )
    passed = not issues
    _emit(passed, issues)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
