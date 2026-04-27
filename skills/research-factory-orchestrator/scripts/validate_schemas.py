#!/usr/bin/env python3
"""Validate all JSON Schemas in ../schemas (structural checks)."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "schemas"
    failed = 0
    for f in sorted(root.glob("*.schema.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "$schema" not in data:
                raise ValueError("missing $schema")
            if data.get("type") != "object":
                raise ValueError("top-level type must be object")
            if "properties" not in data:
                raise ValueError("missing properties")
            print("OK", f.name)
        except Exception as e:
            failed += 1
            print("FAIL", f.name, e, file=sys.stderr)
    if failed:
        return 1
    print("All schema files passed structural validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
