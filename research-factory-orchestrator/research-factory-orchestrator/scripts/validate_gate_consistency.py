#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from runtime.legacy_compat import read_fag_gates

ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); args=ap.parse_args(); rd=Path(args.run_dir)
errors=[]
fg=json.loads((rd/'final-answer-gate.json').read_text(encoding='utf-8')) if (rd/'final-answer-gate.json').exists() else {}
gates, _gs = read_fag_gates(fg if isinstance(fg, dict) else {})
if fg.get('passed') and any(not g.get('passed') for g in gates.values() if isinstance(g,dict) and g.get('status')!='stub_only'):
    errors.append('final_pass_with_failed_gate')
if gates.get('external_delivery_gate',{}).get('status')=='stub_only' and fg.get('passed'):
    errors.append('stub_external_delivery_marked_passed')
html=(rd/'report/full-report.html').read_text(encoding='utf-8',errors='ignore') if (rd/'report/full-report.html').exists() else ''
if 'VALIDATION_GATE: PASSED' in html and ('FAIL' in html or 'TIMEOUT' in html or 'PARTIAL' in html): errors.append('html_validation_pass_conflicts_with_failed_gates')
out={'status':'fail' if errors else 'pass','validator':'validate_gate_consistency','errors':errors}
print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(1 if errors else 0)
