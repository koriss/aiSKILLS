#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shard_ledger")
    args = ap.parse_args()
    data = json.loads(Path(args.shard_ledger).read_text(encoding="utf-8"))
    errors = []
    if data.get("unmerged_count", 0) != 0:
        errors.append("unmerged_count != 0")
    for s in data.get("shards", []):
        if s.get("merge_status") not in ["merged", "not_applicable"]:
            errors.append(f"unmerged shard: {s.get('work_unit_id')} merge_status={s.get('merge_status')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no unmerged shards")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
