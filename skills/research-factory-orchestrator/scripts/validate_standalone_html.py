#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys, json
EXTERNAL_PATTERNS=[re.compile(r'<link\s+[^>]*rel=["\']stylesheet["\']',re.I),re.compile(r'<script\s+[^>]*src=["\']',re.I),re.compile(r'<img\s+[^>]*src=["\'](?!data:|https?://)',re.I),re.compile(r'<link\s+[^>]*href=["\']https?://fonts\.',re.I)]
INLINE_CITE_RE=re.compile(r'<sup\b[^>]*>\s*<a\s+href=["\']#ref-\d+["\'][^>]*>\[\d+\]</a>\s*</sup>',re.I)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('html'); ap.add_argument('--json-out'); args=ap.parse_args()
    text=Path(args.html).read_text(encoding='utf-8',errors='replace'); errors=[]
    if '<meta name="viewport"' not in text: errors.append('missing viewport meta')
    if '<style' not in text: errors.append('missing inline style')
    if 'id="references"' not in text and "id='references'" not in text: errors.append('missing references section')
    if not INLINE_CITE_RE.search(text): errors.append('missing wiki-style inline citations')
    for pat in EXTERNAL_PATTERNS:
        if pat.search(text): errors.append(f'external asset pattern found: {pat.pattern}')
    refs=set(re.findall(r'href=["\']#(ref-\d+)["\']',text,re.I)); ids=set(re.findall(r'id=["\'](ref-\d+)["\']',text,re.I)); missing=refs-ids
    if missing: errors.append('missing reference targets: '+', '.join(sorted(missing)))
    result={'path':args.html,'standalone':not errors,'validated':not errors,'errors':errors}
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 1
    print('OK: standalone HTML validates'); return 0
if __name__=='__main__': raise SystemExit(main())
