#!/usr/bin/env python3
"""P5: compare critical schema fingerprints vs runtime/version.json (CI hook)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRITICAL = [
    ROOT / "scripts" / "validate_logical_consistency.py",
    ROOT / "scripts" / "validate_release.py",
    ROOT / "scripts" / "run_core_validators.py",
    ROOT / "validators" / "core" / "validate_traceability.py",
    ROOT / "validators" / "core" / "validate_delivery_truth.py",
    ROOT / "scripts" / "check_validation_pass.py",
    ROOT / "scripts" / "migrate_validator_invocation.py",
    ROOT / "schemas" / "delivery-manifest.schema.json",
    ROOT / "schemas" / "claim.schema.json",
    ROOT / "contracts" / "handoff-envelope.schema.json",
    ROOT / "contracts" / "capability-token.schema.json",
    ROOT / "contracts" / "severity-matrix.json",
    ROOT / "contracts" / "slo-config.json",
    ROOT / "contracts" / "state-machine.json",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    paths = list(CRITICAL)
    core_dir = ROOT / "schemas" / "core"
    if core_dir.is_dir():
        paths.extend(sorted(core_dir.glob("*.json")))
    cm = ROOT / "schemas" / "contradiction-matrix.schema.json"
    if cm.is_file() and cm not in paths:
        paths.append(cm)
    snap = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths if p.exists()}
    print(json.dumps({"status": "pass", "schema_fingerprints": snap}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
