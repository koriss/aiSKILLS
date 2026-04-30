#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
REQ=["artifact-contract.json","pipeline-stage-contract.json","validator-dag.json","delivery-contract.json","eval-corpus-contract.json","schema-strictness-contract.json"]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("skill_dir"); args=ap.parse_args()
    root=Path(args.skill_dir)/"contracts"; errors=[]
    for name in REQ:
        p=root/name
        if not p.exists(): errors.append(f"missing contract: {name}"); continue
        try: json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"bad JSON {name}: {e}")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: contract registry validates"); return 0
if __name__=="__main__": raise SystemExit(main())
