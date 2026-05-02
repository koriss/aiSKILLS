#!/usr/bin/env python3
"""CLI delivery adapter with optional capability-token verification."""
from pathlib import Path
import argparse, datetime, json
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.capability import verify

ap = argparse.ArgumentParser()
ap.add_argument('--run-dir', required=False)
ap.add_argument('--event-id', required=False)
ap.add_argument('--event-json', required=False)
ap.add_argument('--capability-token', required=False)
ap.add_argument('--action', required=False, default='deliver_external:cli')
args = ap.parse_args()

now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
event = {}
if args.event_json and Path(args.event_json).exists():
    event = json.loads(Path(args.event_json).read_text(encoding='utf-8'))

if args.capability_token:
    tp = Path(args.capability_token)
    token = json.loads(tp.read_text(encoding='utf-8')) if tp.is_file() else {}
    if not verify(token, args.action):
        print(json.dumps({'provider': 'cli', 'status': 'failed', 'reason': 'capability_denied'}, ensure_ascii=False))
        raise SystemExit(1)

_eid = args.event_id or event.get('event_id') or 'unknown'
print(json.dumps({
    'provider': 'cli',
    'event_id': _eid,
    'status': 'stub',
    'stub_delivery': True,
    'real_external_delivery': False,
    'provider_message_id': f'stub:cli:{_eid}',
    'acked_at': now,
}, ensure_ascii=False))
