#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("subagent_plan_or_ledger"); args=ap.parse_args()
    d=json.loads(Path(args.subagent_plan_or_ledger).read_text(encoding="utf-8"))
    n=len(d.get("assignments") or d.get("subagents") or [])
    if n<=1: print(f"single-subagent research invalid: {n}", file=sys.stderr); return 1
    print(f"OK: subagents/assignments = {n}"); return 0
if __name__=="__main__": raise SystemExit(main())
