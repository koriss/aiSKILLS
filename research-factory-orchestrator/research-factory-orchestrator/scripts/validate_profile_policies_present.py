#!/usr/bin/env python3
"""Guard: ``validation-profiles/*.json`` must declare ``source_policy`` and ``delivery_policy``."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_ID = "validate_profile_policies_present"


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
                "summary": "profile policies present",
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    issues: list[dict] = []
    ddir = ROOT / "validation-profiles"
    for p in sorted(ddir.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({"code": "PARSE", "severity": "error", "file": p.name, "detail": str(e)})
            continue
        if not isinstance(d, dict):
            continue
        sp = d.get("source_policy")
        dp = d.get("delivery_policy")
        if not isinstance(sp, dict) or len(sp) < 1:
            issues.append({"code": "PROFILE-MISSING-SOURCE-POLICY", "severity": "error", "file": p.name})
        if not isinstance(dp, dict) or len(dp) < 1:
            issues.append({"code": "PROFILE-MISSING-DELIVERY-POLICY", "severity": "error", "file": p.name})
    passed = not issues
    _emit(passed, issues)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
