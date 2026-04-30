#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("work_unit_plan"); args=ap.parse_args()
    n=len(json.loads(Path(args.work_unit_plan).read_text(encoding="utf-8")).get("work_units",[]))
    if n<=1: print(f"single-work-unit research invalid: {n}", file=sys.stderr); return 1
    print(f"OK: work units = {n}"); return 0
if __name__=="__main__": raise SystemExit(main())
