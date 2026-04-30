#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("watchdog_state")
    args = ap.parse_args()
    data = json.loads(Path(args.watchdog_state).read_text(encoding="utf-8"))
    errors = []
    for k in ["running","stale","failed_retryable","unmerged"]:
        if data.get(k):
            errors.append(f"watchdog has open {k}: {data.get(k)}")
    if data.get("blocked_final_delivery") is True:
        errors.append("watchdog blocks final delivery")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: watchdog all clear")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
