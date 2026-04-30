#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys
ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); args=ap.parse_args(); rd=Path(args.run_dir)
errors=[]
texts=[]
for rel in ['chat/message-004-files.txt','delivery-manifest.json','attachment-ledger.json','report/full-report.html']:
    p=rd/rel
    if p.exists(): texts.append((rel,p.read_text(encoding='utf-8',errors='ignore')))
claim_words=re.compile(r'(zip|archive|архив|research-package\.zip|артефакт[ыов]*\s+отправ)', re.I)
claims=[rel for rel,t in texts if claim_words.search(t)]
if claims and not (rd/'package/research-package.zip').exists(): errors.append({'package_claim_without_zip':claims})
if (rd/'package/research-package.zip').exists() and not (rd/'delivery-acks/OUT-0006.json').exists():
    # warning-level unless final user claim is pass
    gate=json.loads((rd/'final-answer-gate.json').read_text(encoding='utf-8')) if (rd/'final-answer-gate.json').exists() else {}
    if gate.get('status')=='pass': errors.append('final_pass_without_package_ack')
out={'status':'fail' if errors else 'pass','validator':'validate_package_claim_requires_zip','errors':errors}
print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(1 if errors else 0)
