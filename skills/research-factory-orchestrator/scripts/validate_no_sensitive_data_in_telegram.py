#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
EMAIL=re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I); PHONE=re.compile(r'(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)')
def files(path):
    p=Path(path); return [p] if p.is_file() else list(p.rglob("telegram-message-*.txt"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args(); errors=[]
    for p in files(args.path):
        t=p.read_text(encoding="utf-8", errors="ignore")
        if EMAIL.search(t): errors.append(f"{p}: raw email in Telegram")
        if PHONE.search(t): errors.append(f"{p}: possible raw phone in Telegram")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: no sensitive raw contacts in Telegram"); return 0
if __name__=="__main__": raise SystemExit(main())
