#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

BLOCK=['Reasoning:','Chain of thought','hidden scratchpad','internal deliberation']
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    offenders=[]
    for base in ['chat','provider-payloads','outbox']:
        d=root/base
        if not d.exists(): continue
        for p in d.rglob('*'):
            if p.is_file() and p.suffix.lower() in ['.txt','.json','.md']:
                t=p.read_text(encoding='utf-8',errors='ignore')
                if any(b in t for b in BLOCK): offenders.append(str(p.relative_to(root)))
    if offenders:
        print(json.dumps({'status':'fail','code':'F283','validator':'validate_no_reasoning_leak_in_chat_payload','offenders':offenders},ensure_ascii=False)); sys.exit(1)
    print(json.dumps({'status':'pass','validator':'validate_no_reasoning_leak_in_chat_payload'},ensure_ascii=False))
if __name__=='__main__': main()
