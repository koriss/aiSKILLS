#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("subagent_ledger"); args=ap.parse_args()
    d=json.loads(Path(args.subagent_ledger).read_text(encoding="utf-8")); subs=d.get("subagents",[])
    req=d.get("required_quorum", max(2,len(subs))); comp=sum(1 for s in subs if s.get("status")=="completed"); errors=[]
    if len(subs)<=1: errors.append("single-subagent ledger invalid")
    if comp<req: errors.append(f"quorum not met: {comp} < {req}")
    if d.get("quorum_met") is not True: errors.append("quorum_met != true")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: subagent quorum validates"); return 0
if __name__=="__main__": raise SystemExit(main())
