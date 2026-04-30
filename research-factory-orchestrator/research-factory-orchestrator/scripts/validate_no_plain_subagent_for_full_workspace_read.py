#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    policy=json.loads((root/'policies'/'context-acquisition-policy.json').read_text(encoding='utf-8')) if (root/'policies'/'context-acquisition-policy.json').exists() else {'thresholds':{'plain_subagent_full_read_file_limit':100}}
    limit=policy.get('thresholds',{}).get('plain_subagent_full_read_file_limit',100)
    file_count=sum(1 for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    # Skill package itself is allowed to contain policy text; runtime proof is checked only if context-load-request exists.
    req=root/'context'/'context-load-request.json'
    if req.exists():
        data=json.loads(req.read_text(encoding='utf-8'))
        if data.get('mode')=='plain_subagent_read_all' and file_count>limit:
            print(json.dumps({'status':'fail','code':'F274','validator':'validate_no_plain_subagent_for_full_workspace_read','file_count':file_count,'limit':limit},ensure_ascii=False)); sys.exit(1)
    print(json.dumps({'status':'pass','validator':'validate_no_plain_subagent_for_full_workspace_read','file_count':file_count,'limit':limit},ensure_ascii=False))
if __name__=='__main__': main()
