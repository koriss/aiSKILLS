#!/usr/bin/env python3
"""Guard: production mode runs must not advertise scaffold/stub/missing on required features."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_ID = "validate_no_scaffolds_in_production"
_BAD = frozenset({"scaffold", "stub", "missing"})


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
                "summary": "no scaffolds in production",
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
    if mode != "production":
        _emit(True, [])
        return 0
    cfg_path = ROOT / "contracts" / "production-features-required.json"
    if not cfg_path.is_file():
        issues.append({"code": "CONFIG-MISSING", "severity": "error", "detail": str(cfg_path)})
        _emit(False, issues)
        return 1
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    keys = cfg.get("required_features") or []
    ftm_p = rd / "feature-truth-matrix.json"
    if not ftm_p.is_file():
        issues.append({"code": "FTM-MISSING", "severity": "error"})
        _emit(False, issues)
        return 1
    ftm = json.loads(ftm_p.read_text(encoding="utf-8"))
    feats = ftm.get("features") or {}
    for k in keys:
        v = feats.get(k)
        st = ""
        if isinstance(v, dict):
            st = str(v.get("status", "")).lower()
        else:
            st = str(v).lower()
        if st in _BAD:
            issues.append({"code": "PRODUCTION-SCAFFOLD-FEATURE", "severity": "error", "feature": k, "status": st})
    passed = not issues
    _emit(passed, issues)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
