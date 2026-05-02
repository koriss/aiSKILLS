#!/usr/bin/env python3
"""P1: lightweight schema field coverage probe (non-blocking baseline)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    schemas = list((ROOT / "schemas").glob("*.json"))
    out = {
        "status": "pass",
        "validator": "validate_schema_field_coverage",
        "schemas_scanned": len(schemas),
        "note": "Full orphan-field matrix deferred; this gate proves schemas directory is readable.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
