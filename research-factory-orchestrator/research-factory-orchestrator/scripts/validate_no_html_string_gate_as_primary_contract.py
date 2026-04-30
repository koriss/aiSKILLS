#!/usr/bin/env python3
import json, sys, re
from pathlib import Path

def load_json(path, default=None):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return {'__invalid_json__': str(e)}

def emit(status='pass', code='OK', **kw):
    print(json.dumps({'status':status,'code':code,**kw}, ensure_ascii=False, indent=2))
    return 0 if status in ('pass','warning') else 1


def main():
    skill=Path(__file__).resolve().parents[1]
    c=load_json(skill/'contracts/validation-source-of-truth-contract.json', {})
    if not c.get('machine_readable_artifacts_are_primary'):
        return emit('fail','F352', message='validation source-of-truth contract missing')
    core=(skill/'scripts/rfo_v18_core.py').read_text(encoding='utf-8', errors='ignore')
    uses_html_heuristics='VALIDATION_GATE: PASSED' in core or "'Placeholder' in htmltxt" in core
    return emit('warning' if uses_html_heuristics else 'pass','F352', html_heuristics_present=uses_html_heuristics, note='warning only in v18.3.2; refactor planned')
if __name__=='__main__': raise SystemExit(main())

