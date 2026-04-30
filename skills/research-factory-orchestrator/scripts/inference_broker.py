#!/usr/bin/env python3
import argparse, json, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--work-unit-id', default='WU-DRY-001')
    ap.add_argument('--model-call-id', default='MC-DRY-001')
    ap.add_argument('--status', default='complete', choices=['complete','partial','timeout','disconnect','overflow','backend_error'])
    ap.add_argument('--finalize', action='store_true')
    args=ap.parse_args()
    root=Path(args.run_dir); ex=root/'execution'; ex.mkdir(parents=True, exist_ok=True)
    outdir=ex/'model-outputs'; outdir.mkdir(exist_ok=True)
    outpath=outdir/(args.model_call_id+'.jsonl')
    lines=[{'type':'start','model_call_id':args.model_call_id,'work_unit_id':args.work_unit_id,'ts':time.time()}]
    if args.finalize or args.status=='complete': lines.append({'type':'finalize','status':'complete','work_unit_id':args.work_unit_id})
    outpath.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in lines)+'\n', encoding='utf-8')
    rec={'model_call_id':args.model_call_id,'work_unit_id':args.work_unit_id,'model_profile':'dry_run','status':args.status,'output_ref':str(outpath.relative_to(root)),'finalize_seen': any(x.get('type')=='finalize' for x in lines),'idempotency_key':args.work_unit_id+':dry_run:v1'}
    with (ex/'model-call-ledger.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False)+'\n')
    if args.status in ['timeout','disconnect','overflow','backend_error']:
        with (ex/'model-timeout-ledger.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False)+'\n')
    print(json.dumps({'status':'pass','record':rec}, ensure_ascii=False))
if __name__=='__main__': main()
