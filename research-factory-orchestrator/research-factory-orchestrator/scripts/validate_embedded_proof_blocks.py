#!/usr/bin/env python3
from pathlib import Path
import argparse, re, json, sys
REQ=["artifact-manifest-json","provenance-manifest-json","validation-transcript-json","delivery-manifest-json"]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("html"); args=ap.parse_args()
    text=Path(args.html).read_text(encoding="utf-8", errors="ignore"); errors=[]
    for rid in REQ:
        m=re.search(r'<script[^>]+id=["\']'+re.escape(rid)+r'["\'][^>]*>(.*?)</script>', text, re.I|re.S)
        if not m: errors.append(f"missing embedded proof block: {rid}")
        else:
            try: json.loads(m.group(1))
            except Exception as e: errors.append(f"bad JSON in {rid}: {e}")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: embedded proof blocks validate"); return 0
if __name__=="__main__": raise SystemExit(main())
