#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
BAD=[r'не\s+найден[ао]?\s+нигде',r'не\s+существует',r'no\s+such\s+person',r'not\s+found\s+anywhere',r'identity\s+resolved\s+negative']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    text=Path(args.path).read_text(encoding="utf-8", errors="ignore")
    errors=[pat for pat in BAD if re.search(pat,text,re.I)]
    if errors:
        print("overconfident negative identity wording: "+", ".join(errors), file=sys.stderr); return 1
    print("OK: negative identity wording bounded"); return 0
if __name__=="__main__": raise SystemExit(main())
