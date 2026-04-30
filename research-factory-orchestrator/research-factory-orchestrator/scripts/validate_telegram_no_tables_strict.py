#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
TABLE_ROW=re.compile(r'^\s*\|.+\|\s*$', re.M); ASCII=re.compile(r'^\s*\+[-+]+\+\s*$', re.M); CODE_TABLE=re.compile(r'```[\s\S]*?\|[\s\S]*?```', re.I)
def files(path):
    p=Path(path); return [p] if p.is_file() else list(p.rglob("telegram-message-*.txt"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args(); errors=[]
    for p in files(args.path):
        t=p.read_text(encoding="utf-8", errors="ignore")
        if TABLE_ROW.search(t) or ASCII.search(t) or CODE_TABLE.search(t): errors.append(f"{p}: Telegram table detected")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: no Telegram tables"); return 0
if __name__=="__main__": raise SystemExit(main())
