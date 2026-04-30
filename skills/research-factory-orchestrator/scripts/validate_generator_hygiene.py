#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys, json
CURRENT_VERSION='12.0.0-report-delivery-system'
PROTECTED_PREFIXES=('scripts/validate_', 'scripts/security_', 'kb/propaganda-io/_raw/')
STALE_TOKENS=['v4-strict','v5-full-html-report','v6-enforced','v7-proof','v8-identity-package','v9-exhaustive-osint','v10-durable-fusion','v11-self-contained-kb']
def read(p): return p.read_text(encoding='utf-8',errors='replace')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--skill-dir',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--json-out'); args=ap.parse_args()
    root=Path(args.skill_dir); errors=[]; warnings=[]
    vs=root/'scripts'/'validate_skill.py'
    if vs.exists():
        text=read(vs)
        if CURRENT_VERSION in re.findall(r'forbidden.*?\[(.*?)\]', text, flags=re.S)[0] if re.findall(r'forbidden.*?\[(.*?)\]', text, flags=re.S) else False:
            errors.append('current version appears inside validate_skill forbidden list')
        # more direct: only error if current version appears near forbidden list section
        idx=text.find('for forbidden in')
        if idx!=-1 and CURRENT_VERSION in text[idx:idx+1200]: errors.append('current version appears in forbidden loop')
    # stale tokens in runtime docs/source, allowing validator denylist literals and tests that intentionally mention them
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in ['.md','.py','.json','.txt','.html','.yml','.yaml']: continue
        rel=str(p.relative_to(root))
        if rel.startswith('kb/propaganda-io/') or rel.startswith('tests/') or rel.startswith('scripts/validate_'): continue
        text=read(p)
        for token in STALE_TOKENS:
            if token in text: errors.append(f'stale token {token} in {rel}')
    result={'validated':not errors,'errors':errors,'warnings':warnings}
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 1
    print('OK: generator hygiene validates'); return 0
if __name__=='__main__': raise SystemExit(main())
