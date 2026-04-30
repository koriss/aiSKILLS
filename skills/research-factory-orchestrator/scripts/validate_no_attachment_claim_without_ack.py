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
    texts=[]
    for rel in ['chat/chat-message-plan.json','delivery/user-visible-message.txt']:
        p=root/rel
        if p.exists(): texts.append(p.read_text(encoding='utf-8', errors='ignore'))
    joined='\n'.join(texts)
    claims=bool(re.search(r'(во вложени|attached|sent|delivered|переотправ)', joined, re.I))
    delivery=load_json(root/'delivery-manifest.json', {}) or {}
    attach=load_json(root/'attachment-ledger.json', {}) or {}
    ack=delivery.get('delivery_status') in ('sent','delivered') and (attach.get('all_required_sent') or attach.get('attachments'))
    if claims and not ack: return emit('fail','F300', message='attachment/send claim without delivery + attachment ack')
    return emit('pass','F300')
if __name__=='__main__': raise SystemExit(main())

