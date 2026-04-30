#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

# This validator is intentionally about core runtime scripts, not legacy renderer/validator names.
CORE_RUNTIME = [
    'scripts/common_runtime.py',
    'scripts/init_runtime.py',
    'scripts/run_research_factory.py',
    'scripts/runtime_job_worker.py',
    'scripts/outbox_delivery_worker.py',
]
BANNED = [
    re.compile(r'api\.telegram\.org', re.I),
    re.compile(r'sendMessage|sendDocument', re.I),
    re.compile(r'TELEGRAM_[A-Z_]+'),
    re.compile(r'Bot\s+[A-Za-z0-9:_-]+'),
    re.compile(r'providers/telegram|telegram_delivery_adapter', re.I),
    re.compile(r'\btelegram-message-plan\.json\b', re.I),
    re.compile(r'\btelegram-message-\d+\.txt\b', re.I),
]
ALLOWED_LOW_LEVEL = [
    'provider = ev.get("provider") or "cli"',
    'here.parent / "providers" / provider',
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('skill_dir')
    args = ap.parse_args()
    root = Path(args.skill_dir)
    errors = []
    for rel in CORE_RUNTIME:
        path = root / rel
        if not path.exists():
            errors.append(f'missing core runtime script: {rel}')
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for rx in BANNED:
            if rx.search(text):
                errors.append(f'{rel}: provider-specific logic matched {rx.pattern}')
    # Also ensure provider-specific adapters live under providers/, not scripts/.
    for path in sorted((root / 'scripts').glob('*telegram*')):
        if path.name not in {'render_telegram_messages.py', 'split_telegram_messages.py'} and not path.name.startswith('validate_telegram') and not path.name.startswith('validate_no_'):
            errors.append(f'provider-specific script in scripts/: {path.name}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OK: provider-specific delivery logic is not in core runtime')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
