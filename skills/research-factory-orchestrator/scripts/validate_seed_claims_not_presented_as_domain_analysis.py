#!/usr/bin/env python3
import json, sys, re
from pathlib import Path

def load_json(path, default=None):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return {'__invalid_json__': str(e)}

def emit(status='pass', code='OK', **kw):
    print(json.dumps({'status':status,'code':code,**kw}, ensure_ascii=False, indent=2))
    return 0 if status in ('pass','warning') else 1


def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    claims=load_json(root/'claims/claims-registry.json', {}) or {}
    cs=claims.get('claims', []) if isinstance(claims, dict) else []
    seed_only=cs and all(str(c.get('origin','')).startswith('v18_seed') or c.get('source_ids')==['SRC-SEED-001'] for c in cs)
    gate=load_json(root/'final-answer-gate.json', {}) or {}
    if seed_only and gate.get('passed') is True:
        return emit('fail','F312', message='seed-only claims cannot pass as domain analysis')
    return emit('pass','F312')
if __name__=='__main__': raise SystemExit(main())

