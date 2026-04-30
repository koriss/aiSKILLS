#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED_RUN_FILES = [
    'entrypoint-proof.json','runtime-status.json','package/research-package.zip','chat/chat-message-plan.json',
    'outbox/OUT-0001.json','outbox/OUT-0002.json','outbox/OUT-0003.json',
    'delivery-acks/OUT-0001.json','delivery-acks/OUT-0002.json','delivery-acks/OUT-0003.json',
    'delivery-manifest.json','attachment-ledger.json','final-answer-gate.json',
]

def jread(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs-root', required=True); ap.add_argument('--run-dir', required=True); args=ap.parse_args()
    runs_root=Path(args.runs_root); run_dir=Path(args.run_dir); errors=[]
    if not run_dir.exists(): print(f'run_dir missing: {run_dir}', file=sys.stderr); return 1
    job_path=run_dir/'jobs'/'runtime-job.json'
    if not job_path.exists(): print('missing jobs/runtime-job.json', file=sys.stderr); return 1
    job=jread(job_path); job_id=job.get('job_id'); run_id=job.get('run_id')
    if job.get('status')!='done': errors.append(f'job status must be done after worker lifecycle, got {job.get("status")!r}')
    if job.get('runtime_executed') is not True: errors.append('job.runtime_executed must be true')
    if job.get('package_built') is not True: errors.append('job.package_built must be true')
    if job.get('outbox_events') != 3: errors.append('job.outbox_events must equal 3')
    for folder,should_exist in [('done',True),('pending',False),('running',False),('failed',False)]:
        p=runs_root/'queue'/folder/f'{job_id}.json'
        if should_exist and not p.exists(): errors.append(f'job not found in queue/{folder}: {job_id}')
        if not should_exist and p.exists(): errors.append(f'job still/present in queue/{folder}: {job_id}')
    for rel in REQUIRED_RUN_FILES:
        if not (run_dir/rel).exists(): errors.append(f'missing required lifecycle file: {rel}')
    status=jread(run_dir/'runtime-status.json') if (run_dir/'runtime-status.json').exists() else {}
    manifest=jread(run_dir/'delivery-manifest.json') if (run_dir/'delivery-manifest.json').exists() else {}
    gate=jread(run_dir/'final-answer-gate.json') if (run_dir/'final-answer-gate.json').exists() else {}
    if status.get('run_id') != run_id: errors.append('runtime-status run_id mismatch')
    if status.get('state') not in ['delivered','stub_delivered']: errors.append(f'runtime-status state must be delivered/stub_delivered after outbox worker, got {status.get("state")!r}')
    if manifest.get('required_acks_present') is not True: errors.append('delivery-manifest.required_acks_present must be true')
    gates=manifest.get('gates') or {}
    provider=(gates.get('provider_ack_gate') or {}).get('status')
    external=(gates.get('external_delivery_gate') or {}).get('status')
    final_claim=(gates.get('final_user_claim_gate') or {}).get('status')
    if provider != 'pass': errors.append('provider_ack_gate must pass after ACKs')
    if manifest.get('delivery_status') == 'stub_delivered':
        if external != 'stub_only': errors.append('stub lifecycle external_delivery_gate must be stub_only')
        if final_claim != 'stub_only': errors.append('stub lifecycle final_user_claim_gate must be stub_only')
        if manifest.get('delivery_claim_allowed') is not False: errors.append('stub lifecycle must not allow external delivery claim')
        if gate.get('passed') is not False: errors.append('stub lifecycle final-answer-gate.passed must be false')
        if status.get('final_answer_gate_passed') is not False: errors.append('stub lifecycle runtime-status.final_answer_gate_passed must be false')
    elif manifest.get('delivery_status') == 'delivered':
        if external != 'pass' or final_claim != 'pass': errors.append('real lifecycle external/final gates must pass')
        if manifest.get('delivery_claim_allowed') is not True: errors.append('real lifecycle delivery_claim_allowed must be true')
        if gate.get('passed') is not True: errors.append('real lifecycle final-answer-gate.passed must be true')
        if status.get('final_answer_gate_passed') is not True: errors.append('real lifecycle runtime-status.final_answer_gate_passed must be true')
    else:
        errors.append(f'unknown delivery_status: {manifest.get("delivery_status")!r}')
    if errors:
        print('\n'.join(errors), file=sys.stderr); return 1
    print('OK: job lifecycle validates v17.2 proof semantics'); return 0
if __name__=='__main__': raise SystemExit(main())
