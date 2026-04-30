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
    plan=load_json(root/'chat/chat-message-plan.json', {}) or {}
    txt=json.dumps(plan, ensure_ascii=False)
    if re.search(r'(/home/|/tmp/|research-runs/|\.openclaw/)', txt):
        return emit('fail','F330', message='local path appears in user-visible chat plan')
    return emit('pass','F330')
if __name__=='__main__': raise SystemExit(main())

