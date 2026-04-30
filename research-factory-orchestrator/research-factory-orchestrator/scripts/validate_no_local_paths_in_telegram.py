#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
PAT=re.compile(r'(/home/[^ \n]+|/tmp/[^ \n]+|\.\/[^ \n]+|research-runs/[^ \n]+|[A-Za-z]:\\[^ \n]+)')
def files(path):
    p=Path(path); return [p] if p.is_file() else list(p.rglob("telegram-message-*.txt"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args(); errors=[]
    for p in files(args.path):
        t=p.read_text(encoding="utf-8", errors="ignore"); m=PAT.search(t)
        if m: errors.append(f"{p}: local path exposed: {m.group(0)}")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: no local paths in Telegram"); return 0
if __name__=="__main__": raise SystemExit(main())
