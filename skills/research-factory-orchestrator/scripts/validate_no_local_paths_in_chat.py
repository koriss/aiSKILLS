#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys
PAT = re.compile(r'(/home/[^\s]+|/tmp/[^\s]+|/mnt/[^\s]+|[A-Za-z]:\\[^\s]+)')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir')
    args = ap.parse_args()
    root = Path(args.run_dir)
    errors = []
    for p in sorted((root / 'chat').glob('message-*.txt')):
        text = p.read_text(encoding='utf-8', errors='ignore')
        m = PAT.search(text)
        if m:
            errors.append(f'{p.relative_to(root)}: local path exposed: {m.group(0)}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OK: no local paths in chat messages')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
