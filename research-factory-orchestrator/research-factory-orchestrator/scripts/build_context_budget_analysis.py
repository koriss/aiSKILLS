#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib, re, time
sys.dont_write_bytecode=True

def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else root/'context'
    out_dir.mkdir(parents=True, exist_ok=True)
    files=[p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
    total_bytes=sum(p.stat().st_size for p in files)
    est_tokens=max(1,total_bytes//4)
    operational_core=[]
    for rel in ['SKILL.md','scripts/rfo_v18_core.py','scripts/interface_runtime_adapter.py','scripts/runtime_job_worker.py','scripts/outbox_delivery_worker.py','contracts/validator-dag.json']:
        if (root/rel).exists(): operational_core.append(rel)
    result={
      'root':str(root),'total_files':len(files),'total_bytes':total_bytes,'estimated_tokens':est_tokens,
      'active_context_fit':'unlikely' if est_tokens>120000 else 'possible',
      'recommended_mode':'operational_load_plus_index' if est_tokens>120000 else 'operational_load',
      'operational_core':operational_core,
      'limitations':['full raw workspace should not be claimed as active context unless active-context-manifest proves it']
    }
    (out_dir/'context-budget-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'pass','estimated_tokens':est_tokens,'recommended_mode':result['recommended_mode']},ensure_ascii=False))
if __name__=='__main__': main()
