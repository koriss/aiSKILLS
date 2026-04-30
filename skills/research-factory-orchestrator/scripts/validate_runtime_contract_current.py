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
    c=load_json(skill/'contracts/runtime-contract-v18.3.2.json', {})
    if 'run.json' not in c.get('init_runtime_outputs', []):
        return emit('fail','F340', message='current runtime contract does not list init_runtime outputs')
    return emit('pass','F340')
if __name__=='__main__': raise SystemExit(main())

