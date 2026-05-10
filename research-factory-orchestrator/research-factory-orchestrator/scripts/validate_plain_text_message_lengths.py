#!/usr/bin/env python3
from pathlib import Path
import argparse, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message_file")
    ap.add_argument("--hard-limit", type=int, default=3900)
    ap.add_argument("--caption", action="store_true")
    args = ap.parse_args()
    limit = 900 if args.caption else args.hard_limit
    text = Path(args.message_file).read_text(encoding="utf-8", errors="replace")
    length = len(text)
    if length > limit:
        print(f"message too long: {length} > {limit}", file=sys.stderr)
        return 1
    print(f"OK: message length {length}/{limit}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
