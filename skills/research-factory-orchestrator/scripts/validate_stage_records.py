#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage_records_dir")
    args = ap.parse_args()
    root = Path(args.stage_records_dir)
    errors = []
    files = sorted(root.glob("*.json"))
    if not files:
        errors.append("no stage record files")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("status") == "complete":
            if not data.get("artifacts_created"):
                errors.append(f"{f.name}: complete but no artifacts_created")
            for art in data.get("artifacts_created", []):
                if not art.get("sha256"):
                    errors.append(f"{f.name}: artifact without sha256")
                if not art.get("path"):
                    errors.append(f"{f.name}: artifact without path")
            if data.get("validator_status") != "pass":
                errors.append(f"{f.name}: complete but validator_status != pass")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: stage records validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
