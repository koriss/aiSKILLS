#!/usr/bin/env python3
"""Smoke test: adapter → worker → outbox → validate (v19)."""
from pathlib import Path
import argparse, json, tempfile, os, sys
from argparse import Namespace

# Use runtime modules directly (rfo_runtime_core.py only exports main CLI, not sub-commands)
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from runtime.status import VERSION
from runtime.util import now, jw, jr
from runtime.adapter_impl import cmd_adapter
from runtime.worker_impl import cmd_worker
from runtime.outbox_impl import cmd_outbox
from runtime.validate_impl import validate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', default='telegram')
    ap.add_argument('--interface', default='telegram')
    ap.add_argument('--conversation-id', default='test')
    ap.add_argument('--message-id', default='1')
    ap.add_argument('--user-id', default='me')
    ap.add_argument('--task', default='test internal audit target')
    ap.add_argument('--runs-root')
    ap.add_argument('--keep-runs', action='store_true')
    args = ap.parse_args()
    root = Path(args.runs_root or tempfile.mkdtemp(prefix='rfo-v19-smoke-'))
    root.mkdir(parents=True, exist_ok=True)

    report = {
        'smoke_test_version': VERSION,
        'runs_root': str(root),
        'steps': [],
        'started_at': now(),
    }

    def step(name, fn, ns):
        fn(ns)
        report['steps'].append({'name': name, 'status': 'pass', 'finished_at': now()})
        jw(root / 'smoke-test-report.json', report)

    step('interface_runtime_adapter', cmd_adapter, Namespace(
        runs_root=str(root), interface=args.interface, provider=args.provider,
        conversation_id=args.conversation_id, message_id=args.message_id,
        user_id=args.user_id, task=args.task, reply_text='',
        chat_id='', reply_to_message_id='', api_base='',
    ))
    step('runtime_job_worker', cmd_worker, Namespace(
        runs_root=str(root), execute_runtime=True, dry_run=False, mode='research',
    ))
    step('outbox_delivery_worker', cmd_outbox, Namespace(runs_root=str(root)))

    latest = jr(root / 'index/latest.json')
    run_dir = Path(latest['run_dir'])
    code = validate(run_dir)

    report.update({
        'smoke_test_passed': code == 0,
        'run_dir': str(run_dir),
        'run_id': latest['run_id'],
        'run_label': latest['run_label'],
        'finished_at': now(),
    })
    jw(root / 'smoke-test-report.json', report)

    result = {
        'smoke_test_passed': code == 0,
        'runs_root': str(root),
        'run_dir': str(run_dir),
        'final_gate_status': None,
    }
    gate_path = run_dir / 'final-answer-gate.json'
    if gate_path.is_file():
        gate = jr(gate_path, {})
        result['final_gate_status'] = gate.get('status') or gate.get('passed')

    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if code == 0 else 1

if __name__ == '__main__':
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(main() or 0))
