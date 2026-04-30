#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("validation_transcript")
    args = ap.parse_args()
    data = json.loads(Path(args.validation_transcript).read_text(encoding="utf-8"))
    errors = []
    if data.get("all_passed") is not True:
        errors.append("all_passed != true")
    if not data.get("validators"):
        errors.append("validators empty")
    for v in data.get("validators", []):
        if not v.get("name"):
            errors.append("validator missing name")
        if v.get("status") not in ["pass", "blocked"]:
            errors.append(f"validator bad status: {v.get('name')}={v.get('status')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: validation transcript validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
