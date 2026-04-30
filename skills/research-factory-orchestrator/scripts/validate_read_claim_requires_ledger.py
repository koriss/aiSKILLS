#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

PATTERNS=[r'read all files',r'прочитал[аи]?\s+все\s+файлы',r'loaded all files',r'загрузил[аи]?\s+.*в\s+контекст']
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    chat_files=list((root/'chat').glob('*.txt')) if (root/'chat').exists() else []
    claim=False
    for f in chat_files:
        t=f.read_text(encoding='utf-8',errors='ignore').lower()
        if any(re.search(p,t) for p in PATTERNS): claim=True
    if claim and not (root/'context'/'read-ledger.jsonl').exists():
        print(json.dumps({'status':'fail','code':'F271','validator':'validate_read_claim_requires_ledger','error':'read/load all claim without read-ledger'},ensure_ascii=False)); sys.exit(1)
    print(json.dumps({'status':'pass','validator':'validate_read_claim_requires_ledger'},ensure_ascii=False))
if __name__=='__main__': main()
