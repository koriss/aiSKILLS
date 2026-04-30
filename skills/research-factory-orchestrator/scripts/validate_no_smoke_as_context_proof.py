#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    offenders=[]
    for p in list((root/'context').glob('*.json')) if (root/'context').exists() else []:
        t=p.read_text(encoding='utf-8',errors='ignore').lower()
        if 'smoke' in t and ('loaded all' in t or 'full_context_loaded' in t or 'read all' in t): offenders.append(str(p.relative_to(root)))
    if offenders:
        print(json.dumps({'status':'fail','code':'F273','validator':'validate_no_smoke_as_context_proof','offenders':offenders},ensure_ascii=False)); sys.exit(1)
    print(json.dumps({'status':'pass','validator':'validate_no_smoke_as_context_proof'},ensure_ascii=False))
if __name__=='__main__': main()
