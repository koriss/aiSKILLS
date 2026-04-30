#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

BAD = [
    re.compile(r'no\s+(adapter|outbox|return\s+path)', re.I),
    re.compile(r'нет\s+(adapter|адаптер|outbox|return\s+path|пути\s+возврата)', re.I),
    re.compile(r'workaround\s+direct', re.I),
    re.compile(r'напрямую\s+без\s+outbox', re.I),
    re.compile(r'верн(у|ём|ем).*напрямую.*без\s+outbox', re.I | re.S),
]
GOOD = [
    re.compile(r'runtime-job\.json', re.I),
    re.compile(r'outbox', re.I),
    re.compile(r'provider\s+ack', re.I),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    args = ap.parse_args()
    text = Path(args.path).read_text(encoding='utf-8', errors='ignore')
    bad_hits = [rx.pattern for rx in BAD if rx.search(text)]
    if bad_hits:
        print('interface return path missing/bypassed: ' + '; '.join(bad_hits), file=sys.stderr)
        return 1
    if 'interface' in text.lower() or 'adapter' in text.lower() or 'runtime-job' in text.lower():
        if not all(rx.search(text) for rx in GOOD):
            print('interface path mention lacks runtime-job/outbox/provider ack proof', file=sys.stderr)
            return 1
    print('OK: interface return path claim is safe')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
