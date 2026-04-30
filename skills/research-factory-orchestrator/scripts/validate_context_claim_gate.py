#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

def fail(msg):
    print(json.dumps({'status':'fail','validator':'validate_context_claim_gate','error':msg},ensure_ascii=False)); sys.exit(1)
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    ctx=root/'context'
    gate=ctx/'context-claim-gate.json'
    if not gate.exists():
        print(json.dumps({'status':'pass','validator':'validate_context_claim_gate','note':'no runtime context claim gate present in skill package'},ensure_ascii=False)); return
    data=json.loads(gate.read_text(encoding='utf-8'))
    forbidden=data.get('forbidden_claims',[])
    allowed=data.get('allowed_claims',[])
    if data.get('status')=='pass' and any('loaded all' in x.lower() or 'read all' in x.lower() for x in allowed):
        inv=(ctx/'file-inventory.json').exists(); led=(ctx/'read-ledger.jsonl').exists(); man=(ctx/'active-context-manifest.json').exists()
        if not (inv and led and man): fail('full read/load claim allowed without inventory+read-ledger+active-context-manifest')
    print(json.dumps({'status':'pass','validator':'validate_context_claim_gate'},ensure_ascii=False))
if __name__=='__main__': main()
