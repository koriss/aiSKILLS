#!/usr/bin/env python3
"""Emit JSON mapping legacy validator ids to v19 core runner (no mass-rewrite)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Built-in table (docs/v19/migration-map.md); extend as needed.
LEGACY_TO_V19 = {
    "validate_artifact_schema": {"v19": "validate_artifact_schema", "via": "scripts/run_core_validators.py"},
    "validate_traceability": {"v19": "validate_traceability", "via": "scripts/run_core_validators.py"},
    "validate_source_quality": {"v19": "validate_source_quality", "via": "scripts/run_core_validators.py"},
    "validate_claim_status": {"v19": "validate_claim_status", "via": "scripts/run_core_validators.py"},
    "validate_final_answer": {"v19": "validate_final_answer", "via": "scripts/run_core_validators.py"},
    "validate_delivery_truth": {"v19": "validate_delivery_truth", "via": "scripts/run_core_validators.py"},
    "validate_logical_consistency": {"v19": None, "via": "scripts/validate_logical_consistency.py", "note": "v18.7 LC gate; not folded into V1–V6"},
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", "-o", help="Write mapping JSON to this path")
    args = ap.parse_args()
    reg_path = ROOT / "contracts" / "validator-registry.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.is_file() else {}
    rows = []
    for v in reg.get("validators") or []:
        vid = v.get("id") or ""
        rows.append({"id": vid, "path": v.get("path"), "migration": LEGACY_TO_V19.get(vid, {"v19": None, "via": "legacy_dag", "note": "run via runtime/validate_impl.py DAG"})})
    out = {"schema_version": "v19.0", "validators": rows, "runner_profiles": ["mvr", "full-rigor", "propaganda-io", "book-verification"]}
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
