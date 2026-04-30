#!/usr/bin/env python3
from pathlib import Path
import argparse, json, os, re, sys

ABS_PATH = re.compile(r'(^/|^[A-Za-z]:\\)')
REQUIRED = {
    'OUT-0001': {'type': 'send_message', 'payload_kind': 'chat_message', 'file_kind': None},
    'OUT-0002': {'type': 'send_file', 'payload_kind': 'attachment', 'file_kind': 'html_report'},
    'OUT-0003': {'type': 'send_file', 'payload_kind': 'attachment', 'file_kind': 'research_package'},
}

def jread(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir')
    args = ap.parse_args()
    root = Path(args.run_dir)
    errors = []
    policy_path = root / 'outbox' / 'outbox-policy.json'
    if not policy_path.exists():
        errors.append('missing outbox/outbox-policy.json')
    else:
        policy = jread(policy_path)
        if policy.get('only_delivery_worker_can_mark_delivered') is not True:
            errors.append('outbox policy must require delivery worker to mark delivered')
        if policy.get('delivery_claim_requires_ack') is not True:
            errors.append('outbox policy must require ack before delivery claim')
        missing_required = sorted(set(REQUIRED) - set(policy.get('required_events') or []))
        if missing_required:
            errors.append('outbox policy missing required events: ' + ', '.join(missing_required))
    seen = {}
    for event_id, expect in REQUIRED.items():
        path = root / 'outbox' / f'{event_id}.json'
        if not path.exists():
            errors.append(f'{event_id}: missing')
            continue
        ev = jread(path)
        seen[event_id] = ev
        for key in ['run_id','job_id','interface','provider','payload_path','idempotency_key','created_at']:
            if not ev.get(key):
                errors.append(f'{event_id}: missing {key}')
        if ev.get('type') != expect['type']:
            errors.append(f"{event_id}: type {ev.get('type')!r}, expected {expect['type']!r}")
        if ev.get('payload_kind') != expect['payload_kind']:
            errors.append(f"{event_id}: payload_kind {ev.get('payload_kind')!r}, expected {expect['payload_kind']!r}")
        if ev.get('file_kind') != expect['file_kind']:
            errors.append(f"{event_id}: file_kind {ev.get('file_kind')!r}, expected {expect['file_kind']!r}")
        if ev.get('required_for_final_delivery') is not True:
            errors.append(f'{event_id}: required_for_final_delivery must be true')
        status = ev.get('status')
        if status not in ['pending', 'sending', 'sent', 'failed']:
            errors.append(f"{event_id}: invalid status {status!r}")
        if status == 'sent' and not (root / 'delivery-acks' / f'{event_id}.json').exists():
            errors.append(f'{event_id}: marked sent without delivery ack')
        payload_path = ev.get('payload_path') or ''
        if ABS_PATH.search(payload_path):
            errors.append(f'{event_id}: payload_path must be relative, got {payload_path}')
        if '..' in Path(payload_path).parts:
            errors.append(f'{event_id}: payload_path must not escape run_dir')
        if not (root / payload_path).exists():
            errors.append(f'{event_id}: payload target missing: {payload_path}')
        key = ev.get('idempotency_key') or ''
        if ev.get('run_id') and ev['run_id'] not in key:
            errors.append(f'{event_id}: idempotency_key must contain run_id')
        if event_id not in key:
            errors.append(f'{event_id}: idempotency_key must contain event_id')
    keys = [ev.get('idempotency_key') for ev in seen.values()]
    if len(keys) != len(set(keys)):
        errors.append('idempotency_key values must be unique')
    ids = {(ev.get('run_id'), ev.get('job_id'), ev.get('command_id')) for ev in seen.values()}
    if len(ids) > 1:
        errors.append('outbox events have inconsistent run/job/command ids')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OK: outbox event semantics validate')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
