#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
FORBIDDEN_RUNTIME=['LIGHTWEIGHT_RESEARCH','lightweight pipeline is allowed','shortcut pipeline is allowed','economy mode is allowed','skip core stages','skip mandatory stages','/home/node/.openclaw/workspace/research-kb','/home/node/.openclaw/workspace/io-kb-unified','person-privacy-gate','person_privacy_gate']
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--skill-dir',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--json-out'); args=ap.parse_args()
    root=Path(args.skill_dir); errors=[]
    for p in root.rglob('*'):
        if p.is_symlink(): errors.append(f'symlink found: {p.relative_to(root)}')
        if not p.is_file() or p.suffix not in ['.md','.py','.json','.txt','.html','.yml','.yaml']: continue
        rel=str(p.relative_to(root))
        if rel.startswith('kb/propaganda-io/') or rel.startswith('scripts/validate_') or rel.startswith('tests/'):
            continue
        text=p.read_text(encoding='utf-8',errors='replace')
        for token in FORBIDDEN_RUNTIME:
            if token in text: errors.append(f'forbidden runtime token {token} in {rel}')
    for f in (root/'schemas').glob('*.schema.json'):
        try: json.loads(f.read_text(encoding='utf-8'))
        except Exception as e: errors.append(f'invalid schema json {f.name}: {e}')
    result={'validated':not errors,'errors':errors}
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 1
    print('OK: code hygiene validates'); return 0
if __name__=='__main__': raise SystemExit(main())
