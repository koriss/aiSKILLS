#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

BAD = [
    r'прочита(ю|ет|л).*SKILL\.md.*выполн',
    r'read\s+SKILL\.md\s+and\s+execute',
    r'subagent.*SKILL\.md',
    r'plain\s+subagent',
    r'custom\s+prompt.*pipeline',
    r'буду\s+следовать\s+SKILL\.md'
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    text = Path(args.path).read_text(encoding="utf-8", errors="ignore")
    hits = [p for p in BAD if re.search(p, text, re.I | re.S)]
    if hits:
        print("SKILL.md imitation / fake runtime invocation detected: " + ", ".join(hits), file=sys.stderr)
        return 1
    print("OK: no SKILL.md imitation pattern")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
