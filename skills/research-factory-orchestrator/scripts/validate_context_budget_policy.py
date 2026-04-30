#!/usr/bin/env python3
import json, sys, re
from pathlib import Path
sys.dont_write_bytecode = True
FAIL_CODE = 'F227'

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
    root=root_arg(); p=root/'policies/execution-reliability-policy.json'
    if not p.exists(): fail('missing execution-reliability-policy')
    data=read_json(p); limits=data.get('work_unit_limits',{})
    if limits.get('strict_json_single_blob_forbidden') is not True: fail('strict JSON blob must be forbidden')
    if int(limits.get('max_expected_model_runtime_sec',999)) >= 120: fail('model runtime budget must be below 120s idle timeout')
    ok()
if __name__=='__main__': main()
