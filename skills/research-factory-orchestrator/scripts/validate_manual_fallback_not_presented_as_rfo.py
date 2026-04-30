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
    mf=load_json(root/'manual-fallback-ledger.json', {}) or {}
    if mf.get('manual_synthesis_used') and not mf.get('integrated_into_rfo_artifacts') and mf.get('presented_as_rfo_output'):
        return emit('fail','F321', message='manual fallback presented as RFO output')
    return emit('pass','F321')
if __name__=='__main__': raise SystemExit(main())

