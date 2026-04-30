#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("html"); args=ap.parse_args()
    text=Path(args.html).read_text(encoding="utf-8", errors="ignore")
    tables=len(re.findall(r'<table\b', text, re.I)); wrapped=len(re.findall(r'<div[^>]+class=["\'][^"\']*table-wrap', text, re.I)); compact=len(re.findall(r'<table[^>]+class=["\'][^"\']*(compact|card-table)', text, re.I))
    if tables and (wrapped+compact)<tables:
        print(f"mobile-unsafe tables: tables={tables}, wrapped_or_compact={wrapped+compact}", file=sys.stderr); return 1
    print("OK: HTML tables are mobile-safe"); return 0
if __name__=="__main__": raise SystemExit(main())
