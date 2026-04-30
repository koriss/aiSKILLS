#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

TABLE = re.compile(r'^\s*\|.+\|\s*$', re.M)
ABS_PATH = re.compile(r'(^|\s)(/home/[^\s]+|/tmp/[^\s]+|/mnt/[^\s]+|[A-Za-z]:\\[^\s]+)')
DELIVERED_CLAIM = re.compile(r'(доставлен[оы]?|отправлен[оы]?|sent|delivered|attached|прикреплен[оы]?|во вложении)', re.I)

REQUIRED_ATTACHMENTS = {
    'OUT-0002': 'html_report',
    'OUT-0003': 'research_package',
}

def jread(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir')
    args = ap.parse_args()
    root = Path(args.run_dir)
    plan_path = root / 'chat' / 'chat-message-plan.json'
    errors = []
    if not plan_path.exists():
        print('missing chat/chat-message-plan.json', file=sys.stderr)
        return 1
    plan = jread(plan_path)
    for key in ['plain_text_only','mobile_safe','no_tables','no_local_paths','no_premature_delivery_claims']:
        if plan.get(key) is not True:
            errors.append(f'{key} must be true')
    split = plan.get('split_policy') or {}
    if not isinstance(split.get('max_message_chars'), int) or split.get('max_message_chars') > 3500:
        errors.append('split_policy.max_message_chars must be integer <= 3500')
    if split.get('logical_blocks') is not True:
        errors.append('split_policy.logical_blocks must be true')
    policy = plan.get('delivery_claim_policy') or {}
    if policy.get('may_claim_files_delivered') is not False:
        errors.append('delivery_claim_policy.may_claim_files_delivered must be false before ack')
    messages = plan.get('messages') or []
    if not messages:
        errors.append('messages must not be empty')
    for msg in messages:
        rel = msg.get('path') or msg.get('content_path')
        if not rel:
            errors.append(f"message {msg.get('message_id')}: missing path")
            continue
        text_path = root / rel
        if not text_path.exists():
            errors.append(f'{rel}: missing message text')
            continue
        text = text_path.read_text(encoding='utf-8', errors='ignore')
        if TABLE.search(text):
            errors.append(f'{rel}: contains markdown table')
        m = ABS_PATH.search(text)
        if m:
            errors.append(f'{rel}: exposes local path {m.group(2)}')
        if msg.get('contains_delivery_claim') is False and DELIVERED_CLAIM.search(text):
            # allow explicit negative/waiting wording
            low = text.lower()
            allowed = ('только после delivery-ack' in low or 'после delivery-ack' in low or 'waiting' in low or 'ожида' in low)
            if not allowed:
                errors.append(f'{rel}: likely premature delivery claim')
    attachments = plan.get('attachments') or []
    found = {a.get('event_id'): a.get('kind') for a in attachments}
    for event_id, kind in REQUIRED_ATTACHMENTS.items():
        if found.get(event_id) != kind:
            errors.append(f'missing required attachment mapping {event_id} -> {kind}')
        outbox = root / 'outbox' / f'{event_id}.json'
        if outbox.exists():
            ev = jread(outbox)
            if ev.get('payload_path') != next((a.get('path') for a in attachments if a.get('event_id') == event_id), None):
                errors.append(f'{event_id}: attachment path does not match outbox payload_path')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OK: chat message plan semantics validate')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
