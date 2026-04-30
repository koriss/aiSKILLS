#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("matches_json"); args=ap.parse_args()
    data=json.loads(Path(args.matches_json).read_text(encoding="utf-8")); matches=data.get("matches",data if isinstance(data,list) else []); errors=[]
    for m in matches:
        for k in ["kb_record_id","kb_source","matched_text","match_reason","confidence","safe_use"]:
            if k not in m or m.get(k) in [None,""]: errors.append(f"match missing {k}: {m}")
        if m.get("safe_use")!="analytic_classification_only": errors.append(f"bad safe_use: {m.get('safe_use')}")
    if errors:
        print("\n".join(errors),file=sys.stderr); return 1
    print("OK: IO method matches validate"); return 0
if __name__=="__main__": raise SystemExit(main())
