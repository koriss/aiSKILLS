#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); args=ap.parse_args(); rd=Path(args.run_dir)
errors=[]
for rel in ['late-results-ledger.jsonl','amendment-ledger.jsonl','work-queue/work-unit-ledger.json']:
    if not (rd/rel).exists(): errors.append({'missing':rel})
html=(rd/'report/full-report.html').read_text(encoding='utf-8',errors='ignore') if (rd/'report/full-report.html').exists() else ''
if 'TIMEOUT' in html and 'VALIDATION_GATE: PASSED' in html: errors.append('timeout_promoted_to_validation_pass')
out={'status':'fail' if errors else 'pass','validator':'validate_late_results_protocol','errors':errors}
print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(1 if errors else 0)
