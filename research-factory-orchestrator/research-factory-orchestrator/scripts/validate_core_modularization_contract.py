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
    skill=Path(__file__).resolve().parents[1]
    req=['runtime/adapter.py','runtime/worker.py','runtime/outbox.py','runtime/validation.py','runtime/packaging.py','runtime/smoke.py','contracts/core-boundary-contract.json']
    missing=[r for r in req if not (skill/r).exists()]
    if missing: return emit('fail','F350', missing=missing)
    return emit('pass','F350', note='compatibility god module still exists; bounded wrappers/contracts present')
if __name__=='__main__': raise SystemExit(main())

