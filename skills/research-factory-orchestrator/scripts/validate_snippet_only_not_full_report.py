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
    aq=load_json(root/'acquisition/source-acquisition-results.json', {}) or {}
    full=aq.get('fulltext_sources', 0) if isinstance(aq, dict) else 0
    snippets=aq.get('snippet_only_sources', 0) if isinstance(aq, dict) else 0
    gate=load_json(root/'final-answer-gate.json', {}) or {}
    if snippets and not full and gate.get('passed') is True:
        return emit('fail','F322', message='snippet-only acquisition cannot support full final gate')
    return emit('pass','F322')
if __name__=='__main__': raise SystemExit(main())

