#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("claims_registry"); args=ap.parse_args()
    d=json.loads(Path(args.claims_registry).read_text(encoding="utf-8")); claims=d.get("claims", d if isinstance(d,list) else []); errors=[]
    for c in claims:
        typ=c.get("claim_type") or c.get("verification_status"); srcs=c.get("source_ids") or c.get("supporting_sources") or []
        if typ=="confirmed_fact" and len(set(srcs))<2 and c.get("single_source_primary") is not True:
            errors.append(f"{c.get('claim_id','?')}: confirmed_fact requires 2 sources or single_source_primary=true")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: confirmed facts have source support"); return 0
if __name__=="__main__": raise SystemExit(main())
