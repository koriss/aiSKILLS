#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    text = Path(args.path).read_text(encoding="utf-8", errors="ignore")
    if re.search(r'manual_check_passed', text, re.I):
        print("manual_check_passed is not a final validator", file=sys.stderr)
        return 1
    print("OK: no manual_check_passed final proof")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
