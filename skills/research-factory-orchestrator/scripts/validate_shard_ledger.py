#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

BAD_FINAL = {"running","stale","failed_retryable","missing_required_artifacts","unmerged"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shard_ledger")
    args = ap.parse_args()
    data = json.loads(Path(args.shard_ledger).read_text(encoding="utf-8"))
    errors = []
    if data.get("open_retryable_count", 0) != 0:
        errors.append("open_retryable_count != 0")
    if data.get("unmerged_count", 0) != 0:
        errors.append("unmerged_count != 0")
    if data.get("complete") is not True:
        errors.append("shard ledger complete != true")
    for s in data.get("shards", []):
        if s.get("status") in BAD_FINAL:
            errors.append(f"bad final shard status: {s.get('work_unit_id')}={s.get('status')}")
        if s.get("status") == "complete" and s.get("validator_status") != "pass":
            errors.append(f"complete shard without validator pass: {s.get('work_unit_id')}")
        if s.get("status") == "complete" and s.get("merge_status") != "merged":
            errors.append(f"complete shard not merged: {s.get('work_unit_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: shard ledger validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
