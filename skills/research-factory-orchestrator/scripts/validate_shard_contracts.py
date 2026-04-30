#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shard_contracts")
    args = ap.parse_args()
    data = json.loads(Path(args.shard_contracts).read_text(encoding="utf-8"))
    contracts = data.get("contracts", data if isinstance(data, list) else [])
    errors = []
    if not contracts:
        errors.append("contracts empty")
    for c in contracts:
        wid = c.get("work_unit_id")
        for k in ["objective","coverage_categories","required_outputs","validators","merge_target","done_definition"]:
            if not c.get(k):
                errors.append(f"{wid}: missing/empty {k}")
        if not c.get("forbidden_completion"):
            errors.append(f"{wid}: missing forbidden_completion")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: shard contracts validate")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
