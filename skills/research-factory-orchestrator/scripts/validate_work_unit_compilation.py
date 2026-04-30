#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("work_unit_plan"); ap.add_argument("--min-work-units", type=int, default=8); args=ap.parse_args()
    d=json.loads(Path(args.work_unit_plan).read_text(encoding="utf-8")); wus=d.get("work_units",[]); errors=[]
    if len(wus)<args.min_work_units: errors.append(f"too few work units: {len(wus)} < {args.min_work_units}")
    ids=[w.get("work_unit_id") for w in wus]
    if len(ids)!=len(set(ids)): errors.append("duplicate work_unit_id")
    for w in wus:
        for f in ["work_unit_id","axis","objective","status","required_outputs"]:
            if f not in w: errors.append(f"{w.get('work_unit_id','?')}: missing {f}")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: work-unit compilation validates"); return 0
if __name__=="__main__": raise SystemExit(main())
