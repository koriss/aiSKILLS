#!/usr/bin/env python3
"""Guard: every ``contracts/*.json`` (root only) with a ``version`` field must be v19-era.

Phase 6 T6.7 — excludes ``contracts/legacy/**`` and schema files without ``version``.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_ID = "validate_active_contract_versions"


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
                "summary": "active contract versions",
            },
            ensure_ascii=False,
        )
    )


def _ok_version(v: object) -> bool:
    s = str(v).strip()
    return bool(re.match(r"^v?19\.", s))


def main() -> int:
    issues: list[dict] = []
    contracts = ROOT / "contracts"
    for p in sorted(contracts.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({"code": "PARSE", "severity": "error", "file": p.name, "detail": str(e)})
            continue
        if not isinstance(d, dict) or "version" not in d:
            continue
        if d.get("unversioned_runtime_contract") is True:
            continue
        if not _ok_version(d["version"]):
            issues.append(
                {
                    "code": "CONTRACT-VERSION-DRIFT-NON-V19-ACTIVE",
                    "severity": "error",
                    "file": p.name,
                    "version": d.get("version"),
                    "detail": "move to contracts/legacy/ or bump to 19.x",
                }
            )
    passed = not issues
    _emit(passed, issues)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
