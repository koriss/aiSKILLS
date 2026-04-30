#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
RANK_CAPS = {'fetch_fulltext_ok':'E5','archive_available':'E4','search_snippet_only':'E1','auth_required':'E0','fetch_blocked':'E0','fetch_timeout':'E0','permanent_unavailable':'E0'}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--source-id', default='SRC-DRY-001')
    ap.add_argument('--url', default='about:blank')
    ap.add_argument('--state', default='search_snippet_only')
    args=ap.parse_args()
    root=Path(args.run_dir); out=root/'acquisition'; out.mkdir(parents=True, exist_ok=True)
    rec={'source_id':args.source_id,'url':args.url,'attempts':[{'method':'dry_run','status':args.state}], 'final_state':args.state,'evidence_rank_cap':RANK_CAPS.get(args.state,'E0'),'coverage_gap':args.state!='fetch_fulltext_ok'}
    (out/'source-acquisition-results.json').write_text(json.dumps({'results':[rec]}, ensure_ascii=False, indent=2), encoding='utf-8')
    if rec['coverage_gap']:
        gap={'gap_id':'GAP-DRY-001','claim_id':'CLM-UNKNOWN','source_candidate':args.url,'failure_class':args.state,'fallbacks_tried':['dry_run'],'best_available_state':args.state,'impact':'claim cannot be confirmed by this source','recommended_next_action':'find alternative source or provide manual source packet'}
        (out/'source-gap-ledger.json').write_text(json.dumps({'gaps':[gap]}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status':'pass','result':rec}, ensure_ascii=False))
if __name__=='__main__': main()
