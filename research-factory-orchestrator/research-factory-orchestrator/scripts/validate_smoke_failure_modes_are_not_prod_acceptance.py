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
    # Governance validator: passes if contracts explicitly isolate smoke/failure harness from prod acceptance.
    c=load_json(root/'contracts/smoke-run-contract.json', None) or load_json(Path(__file__).resolve().parents[1]/'contracts/smoke-run-contract.json', {})
    if not c or c.get('smoke_is_harness_only') is not True:
        return emit('fail','F351', message='smoke/failure harness not isolated from prod acceptance')
    return emit('pass','F351')
if __name__=='__main__': raise SystemExit(main())

