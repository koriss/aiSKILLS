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
    delivery=load_json(root/'delivery-manifest.json', {}) or {}
    attach=load_json(root/'attachment-ledger.json', {}) or {}
    if delivery.get('delivery_status') in ('sent','delivered') and not (attach.get('attachments') or attach.get('all_required_sent')):
        return emit('fail','F301', message='delivery sent/delivered without attachment ledger evidence')
    return emit('pass','F301')
if __name__=='__main__': raise SystemExit(main())

