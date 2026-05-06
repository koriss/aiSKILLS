#!/usr/bin/env python3
"""Guard: profile.active_validators ⊆ validator-registry.json (RFO v19.2.0).

Closes failure code PROFILE-VALIDATOR-DRIFT (Phase 4C P1).

Negative requirements enforced:
  * every validator named under contracts/run-profiles.json:profiles.*.active_validators
    must appear in contracts/validator-registry.json:validators[].id;
  * registry IDs must point to scripts/<id>.py files that actually exist on disk;
  * runner-imperative ``run_dir_first`` set in runtime/validate_impl.py must be
    a subset of registry IDs (no validators invoked outside the registry).

stdlib-only, fail-closed, JSON envelope on stdout.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VALIDATOR_ID = "validate_profile_validator_alignment"


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> int:
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
    return 0 if not blocking else 1


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    issues: list[dict] = []
    warnings: list[dict] = []

    profiles_path = root / "contracts" / "run-profiles.json"
    registry_path = root / "contracts" / "validator-registry.json"
    validate_impl_path = root / "runtime" / "validate_impl.py"

    if not profiles_path.is_file():
        return _emit(False, True, [{"code": "RUN-PROFILES-MISSING", "severity": "error", "detail": str(profiles_path)}], [], "missing run-profiles.json")
    if not registry_path.is_file():
        return _emit(False, True, [{"code": "VALIDATOR-REGISTRY-MISSING", "severity": "error", "detail": str(registry_path)}], [], "missing validator-registry.json")
    if not validate_impl_path.is_file():
        return _emit(False, True, [{"code": "VALIDATE-IMPL-MISSING", "severity": "error", "detail": str(validate_impl_path)}], [], "missing runtime/validate_impl.py")

    try:
        profiles_doc = json.loads(profiles_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _emit(False, True, [{"code": "RUN-PROFILES-PARSE", "severity": "error", "detail": str(e)}], [], "run-profiles.json parse error")
    try:
        registry_doc = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _emit(False, True, [{"code": "VALIDATOR-REGISTRY-PARSE", "severity": "error", "detail": str(e)}], [], "validator-registry.json parse error")

    registry_ids = {v.get("id"): v for v in registry_doc.get("validators", []) if isinstance(v, dict)}
    for vid, entry in registry_ids.items():
        rel = entry.get("path", "")
        if not rel or not (root / rel).is_file():
            issues.append({"code": "REGISTRY-VALIDATOR-PATH-MISSING", "severity": "error", "vid": vid, "detail": f"path={rel!r} not found"})

    profiles = profiles_doc.get("profiles") or {}
    for pname, pcfg in profiles.items():
        active = pcfg.get("active_validators") if isinstance(pcfg, dict) else None
        if not isinstance(active, list) or not active:
            warnings.append({"code": "PROFILE-NO-ACTIVE-VALIDATORS", "severity": "warning", "profile": pname})
            continue
        for vid in active:
            if vid not in registry_ids:
                issues.append({"code": "PROFILE-VALIDATOR-DRIFT", "severity": "error", "profile": pname, "vid": vid, "detail": f"profile lists {vid!r}, missing from validator-registry.json"})

    text = validate_impl_path.read_text(encoding="utf-8")
    m = re.search(r"run_dir_first\s*=\s*\{([^}]*)\}", text, flags=re.S)
    if not m:
        warnings.append({"code": "RUN-DIR-FIRST-NOT-FOUND", "severity": "warning", "detail": "run_dir_first set not located in validate_impl.py"})
    else:
        body = m.group(1)
        ids_in_set = set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"', body))
        for vid in sorted(ids_in_set):
            if vid not in registry_ids:
                issues.append({"code": "RUNNER-IMPERATIVE-VALIDATOR-NOT-IN-REGISTRY", "severity": "error", "vid": vid, "detail": f"runtime/validate_impl.py invokes {vid!r} but it is missing from validator-registry.json"})

    blocking = any(i.get("severity") == "error" for i in issues)
    return _emit(not blocking, blocking, issues, warnings, "profile↔registry alignment")


if __name__ == "__main__":
    raise SystemExit(main())
