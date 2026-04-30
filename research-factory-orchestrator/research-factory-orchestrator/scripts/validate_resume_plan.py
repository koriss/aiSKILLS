#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("resume_plan")
    args = ap.parse_args()
    data = json.loads(Path(args.resume_plan).read_text(encoding="utf-8"))
    errors = []
    if data.get("work_units_to_retry") and not data.get("next_actions"):
        errors.append("work_units_to_retry present but next_actions empty")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: resume plan validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
