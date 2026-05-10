#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

BAD = [
    re.compile(r'api\.telegram\.org', re.I),
    re.compile(r'sendMessage|sendDocument', re.I),
    re.compile(r'TELEGRAM_[A-Z_]+'),
    re.compile(r'research\s+runtime\s+calls\s+outbound\s+chat\s+api', re.I),
    re.compile(r'runtime\s+hardcodes?\s+outbound\s+provider', re.I),
    re.compile(r'outbound\s+send\s+directly\s+from\s+runtime', re.I),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    args = ap.parse_args()
    text = Path(args.path).read_text(encoding='utf-8', errors='ignore')
    hits = [rx.pattern for rx in BAD if rx.search(text)]
    if hits:
        print('provider-specific delivery hardcode detected: ' + '; '.join(hits), file=sys.stderr)
        return 1
    print('OK: no provider-specific hardcode in text')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
