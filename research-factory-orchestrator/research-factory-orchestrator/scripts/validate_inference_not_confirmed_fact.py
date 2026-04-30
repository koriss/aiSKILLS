#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys
PAT=re.compile(r'(estimated|approx|примерно|около|выведен|derived|inferred|оценка|косвен|calculated)', re.I)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("claims_registry"); args=ap.parse_args()
    d=json.loads(Path(args.claims_registry).read_text(encoding="utf-8")); claims=d.get("claims", d if isinstance(d,list) else []); errors=[]
    for c in claims:
        typ=c.get("claim_type") or c.get("verification_status"); text=str(c.get("text") or c.get("claim") or "")
        if typ=="confirmed_fact" and (c.get("derived") or c.get("inference") or PAT.search(text)):
            errors.append(f"{c.get('claim_id','?')}: derived/estimated claim labelled confirmed_fact")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: derived inferences are not confirmed_fact"); return 0
if __name__=="__main__": raise SystemExit(main())
