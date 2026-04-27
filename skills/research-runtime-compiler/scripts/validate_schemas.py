#!/usr/bin/env python3
import json
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parents[1] / "schemas"
    failed = 0
    for schema_file in sorted(root.glob("*.schema.json")):
        try:
            data = json.loads(schema_file.read_text(encoding="utf-8"))
            for key in ["$schema", "type", "properties"]:
                if key not in data:
                    raise ValueError(f"missing '{key}'")
            if data["type"] != "object":
                raise ValueError("top-level type must be object")
            if "required" in data and not isinstance(data["required"], list):
                raise ValueError("'required' must be list")
            print(f"OK  {schema_file.name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {schema_file.name}: {exc}")
    if failed:
        raise SystemExit(1)
    print("All schemas valid.")

if __name__ == "__main__":
    main()
