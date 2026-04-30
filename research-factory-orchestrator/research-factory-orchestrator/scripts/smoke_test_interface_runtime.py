#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, json, tempfile, os, sys
from argparse import Namespace
core_path = Path(__file__).resolve().parent / 'rfo_v18_core.py'
spec = importlib.util.spec_from_file_location('rfo_v18_core', core_path)
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--provider', default='telegram'); ap.add_argument('--interface', default='telegram')
    ap.add_argument('--conversation-id', default='test'); ap.add_argument('--message-id', default='1'); ap.add_argument('--user-id', default='me')
    ap.add_argument('--task', default='test internal audit target'); ap.add_argument('--runs-root'); ap.add_argument('--keep-runs', action='store_true')
    args=ap.parse_args(); root=Path(args.runs_root or tempfile.mkdtemp(prefix='rfo-v18-smoke-')); root.mkdir(parents=True, exist_ok=True)
    report={'smoke_test_version':core.VERSION,'runs_root':str(root),'steps':[],'started_at':core.now()}
    def step(name, fn, ns):
        fn(ns); report['steps'].append({'name':name,'status':'pass','finished_at':core.now()}); core.jw(root/'smoke-test-report.json', report)
    step('interface_runtime_adapter', core.cmd_adapter, Namespace(runs_root=str(root),interface=args.interface,provider=args.provider,conversation_id=args.conversation_id,message_id=args.message_id,user_id=args.user_id,task=args.task,reply_text=''))
    step('runtime_job_worker', core.cmd_worker, Namespace(runs_root=str(root),execute_runtime=True,dry_run=False))
    step('outbox_delivery_worker', core.cmd_outbox, Namespace(runs_root=str(root)))
    latest=core.jr(root/'index/latest.json'); run_dir=Path(latest['run_dir']); code=core.validate(run_dir)
    if code: return int(code)
    gate=core.jr(run_dir/'final-answer-gate.json')
    report.update({'smoke_test_passed':True,'run_dir':str(run_dir),'run_id':latest['run_id'],'run_label':latest['run_label'],'final_answer_gate':gate,'finished_at':core.now()})
    core.jw(root/'smoke-test-report.json', report)
    print(json.dumps({'smoke_test_passed':True,'runs_root':str(root),'run_dir':str(run_dir),'final_gate_status':gate.get('status')}, ensure_ascii=False, indent=2), flush=True)
    return 0
if __name__=='__main__':
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(int(code or 0))
