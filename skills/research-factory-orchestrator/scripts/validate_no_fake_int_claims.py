#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

BAD = [
    r"SIGINT\s+confirms",
    r"HUMINT\s+(source\s+)?confirms",
    r"MASINT\s+indicates",
    r"ELINT\s+shows",
    r"COMINT\s+(intercept|proves|confirms)",
    r"ACINT\s+confirms",
    r"RADINT\s+confirms",
    r"NUCINT\s+confirms",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text_file")
    args = ap.parse_args()
    txt = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
    errors = []
    for pat in BAD:
        if re.search(pat, txt, re.I):
            errors.append(f"fake/direct INT claim pattern found: {pat}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no fake INT claims detected")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
