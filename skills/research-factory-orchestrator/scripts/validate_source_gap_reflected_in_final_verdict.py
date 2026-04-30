#!/usr/bin/env python3
import json, sys, re
from pathlib import Path
sys.dont_write_bytecode = True
FAIL_CODE = 'F207'

def read_json(path):
    with Path(path).open('r', encoding='utf-8') as f: return json.load(f)
def read_jsonl(path):
    p=Path(path)
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        line=line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: out.append({'__bad_jsonl__': line})
    return out
def fail(msg):
    print(json.dumps({'status':'fail','code':FAIL_CODE,'message':msg}, ensure_ascii=False)); sys.exit(1)
def ok(extra=None):
    x={'status':'pass','code':FAIL_CODE}
    if extra: x.update(extra)
    print(json.dumps(x, ensure_ascii=False)); sys.exit(0)
def root_arg():
    return Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')

def main():
    root=root_arg(); gaps_path=root/'acquisition/source-gap-ledger.json'
    gate_path=root/'final-answer-gate.json'
    if not gaps_path.exists() or not gate_path.exists(): ok({'note':'no gaps or no final gate'})
    gaps=read_json(gaps_path).get('gaps',[]); gate=read_json(gate_path)
    capped=set(gate.get('source_acquisition_gate',{}).get('claims_capped_due_to_source_gaps',[])+gate.get('execution_reliability_gate',{}).get('claims_capped_due_to_execution',[]))
    for g in gaps:
        cid=g.get('claim_id')
        if cid and cid not in ['CLM-UNKNOWN'] and cid not in capped: fail('source gap not reflected in claim caps: '+cid)
    ok({'gaps':len(gaps)})
if __name__=='__main__': main()
