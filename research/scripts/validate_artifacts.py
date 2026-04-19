#!/usr/bin/env python3
"""
Validate research JSON artifacts against schemas/research/*.schema.json
Uses jsonschema if installed; otherwise prints a warning and checks files are valid JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    try:
        import jsonschema
    except ImportError:
        jsonschema = None  # type: ignore

    if len(sys.argv) < 2:
        print("Usage: python3 validate_artifacts.py <file.json> [file2.json ...]")
        sys.exit(2)

    files = [Path(p) for p in sys.argv[1:]]
    for f in files:
        if not f.exists():
            print(f"ERROR: missing {f}")
            sys.exit(1)
        data = load_json(f)
        print(f"OK JSON: {f}")

    if jsonschema is None:
        print("WARN: jsonschema not installed; skipping schema validation (pip install jsonschema)")
        sys.exit(0)

    validators = [
        ("final-report", SCHEMA_DIR / "final-report.schema.json"),
        ("subagent-results", SCHEMA_DIR / "subagent-results.schema.json"),
        ("execution-log", SCHEMA_DIR / "execution-log.schema.json"),
        ("quality-review", SCHEMA_DIR / "quality-review.schema.json"),
    ]

    for f in files:
        name = f.name.lower().replace("_", "-")
        key = None
        schema_path = None
        for k, sp in validators:
            if k in name:
                key = k
                schema_path = sp
                break
        if not key:
            print(f"SKIP schema match: {f.name}")
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(load_json(f), schema)
        print(f"OK schema ({key}): {f}")

    print("OK: all matched files validated against JSON Schema")


if __name__ == "__main__":
    main()
