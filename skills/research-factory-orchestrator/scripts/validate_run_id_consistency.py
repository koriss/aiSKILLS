#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

CORE_FILES = [
    'interface/interface-request.json',
    'interface/normalized-command.json',
    'jobs/runtime-job.json',
    'run.json',
    'entrypoint-proof.json',
    'runtime-status.json',
    'delivery-manifest.json',
    'attachment-ledger.json',
    'final-answer-gate.json',
]

OPTIONAL_GLOBS = [
    'outbox/OUT-*.json',
    'delivery-acks/OUT-*.json',
]

def jread(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir')
    args = ap.parse_args()
    root = Path(args.run_dir)
    errors = []
    ids = {}
    for rel in CORE_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f'{rel}: missing')
            continue
        try:
            data = jread(path)
        except Exception as exc:
            errors.append(f'{rel}: bad JSON: {exc}')
            continue
        for key in ['run_id', 'job_id', 'command_id']:
            val = data.get(key)
            if not val and key == 'command_id' and rel == 'interface/interface-request.json':
                # older interface-request files may omit command_id, but stage07 should normally include it
                pass
            if not val:
                errors.append(f'{rel}: missing {key}')
                continue
            ids.setdefault(key, val)
            if ids[key] != val:
                errors.append(f'{rel}: {key}={val!r}, expected {ids[key]!r}')
    for pattern in OPTIONAL_GLOBS:
        for path in sorted(root.glob(pattern)):
            try:
                data = jread(path)
            except Exception as exc:
                errors.append(f'{path.relative_to(root)}: bad JSON: {exc}')
                continue
            for key in ['run_id', 'job_id', 'command_id']:
                if key in data and ids.get(key) and data.get(key) != ids[key]:
                    errors.append(f'{path.relative_to(root)}: {key}={data.get(key)!r}, expected {ids[key]!r}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('OK: run/job/command ids are consistent')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
