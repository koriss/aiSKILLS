#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

PAT = re.compile(r'(face[- ]?match|biometric|лиц[оа].{0,40}совпал|модель.{0,40}узнал|по фото.{0,40}подтвержд)', re.I | re.S)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    text = Path(args.path).read_text(encoding="utf-8", errors="ignore")
    if PAT.search(text):
        print("biometric/face-match identity claim detected", file=sys.stderr)
        return 1
    print("OK: no biometric identity claim")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
