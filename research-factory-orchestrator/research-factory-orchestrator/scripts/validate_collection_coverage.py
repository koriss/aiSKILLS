#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--result", required=True); args=ap.parse_args()
    c=json.loads(Path(args.contract).read_text(encoding="utf-8")); r=json.loads(Path(args.result).read_text(encoding="utf-8")); errors=[]
    if r.get("work_units_completed",0)<c.get("minimum_work_units",8): errors.append("minimum work units not met")
    if r.get("collection_work_units_completed",0)<c.get("minimum_collection_work_units",6): errors.append("minimum collection work units not met")
    missing=set(c.get("minimum_search_modes",[]))-set(r.get("search_modes_present",[]))
    if missing: errors.append("missing search modes: "+", ".join(sorted(missing)))
    if len(set(r.get("source_families_present",[])))<c.get("minimum_source_families",5): errors.append("minimum source families not met")
    if r.get("independent_sources_count",0)<c.get("minimum_independent_sources",20): errors.append("minimum independent sources not met")
    if r.get("passed") is not True: errors.append("coverage result passed != true")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: collection coverage validates"); return 0
if __name__=="__main__": raise SystemExit(main())
