#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--json-file",required=True); ap.add_argument("--root",required=True); args=ap.parse_args()
    root=Path(args.root); data=json.loads(Path(args.json_file).read_text(encoding="utf-8")); errors=[]
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ["path","artifact_path","file_path","html_report_path","zip_path"] and isinstance(v,str):
                    if v.startswith(("http://","https://")): continue
                    if v.startswith("/"): errors.append(f"absolute artifact path not allowed: {k}={v}")
                    elif not (root/v).exists(): errors.append(f"dangling artifact path: {k}={v}")
                else: walk(v)
        elif isinstance(x,list):
            for y in x: walk(y)
    walk(data)
    if errors:
        print("\n".join(errors),file=sys.stderr); return 1
    print("OK: no dangling artifact links"); return 0
if __name__=="__main__": raise SystemExit(main())
