#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("retry_ledger")
    args = ap.parse_args()
    data = json.loads(Path(args.retry_ledger).read_text(encoding="utf-8"))
    errors = []
    if data.get("open_retries", 0) != 0:
        errors.append("open_retries != 0")
    for r in data.get("retries", []):
        if r.get("status") in ["open","running","failed_retryable"]:
            errors.append(f"retry not closed: {r.get('work_unit_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: retry ledger validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
