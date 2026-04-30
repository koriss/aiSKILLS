#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

RUNTIME_COMMAND = re.compile(r'/research(?:_factory_orchestrator)?', re.I)
DIRECT_TABLE = re.compile(r'^\s*\|.+\|\s*$', re.M)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message")
    args = ap.parse_args()
    text = Path(args.message).read_text(encoding="utf-8", errors="ignore")
    if RUNTIME_COMMAND.search(text) and DIRECT_TABLE.search(text):
        print("direct interface response with table for runtime command", file=sys.stderr)
        return 1
    if "full pipeline" in text.lower() and "rendered_by" not in text.lower():
        print("runtime claim appears to bypass renderer marker", file=sys.stderr)
        return 1
    print("OK: no direct interface response bypass detected")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
