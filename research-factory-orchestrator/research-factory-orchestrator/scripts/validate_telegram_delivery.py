#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re,sys
HTML_TAG=re.compile(r'</?(b|i|u|s|a|code|pre|blockquote|span|div|p|br)\b[^>]*>',re.I)
MD_LINK=re.compile(r'\[[^\]]+\]\([^)]+\)')
MD_TABLE_ROW=re.compile(r'^\s*\|.+\|\s*$',re.M)
MARKDOWN_BOLD=re.compile(r'(\*\*|__)[^*_]+(\*\*|__)')
def validate_plain(text):
    errors=[]
    if HTML_TAG.search(text): errors.append('contains HTML-like markup')
    if MD_LINK.search(text): errors.append('contains markdown link')
    if MARKDOWN_BOLD.search(text): errors.append('contains markdown bold/underline')
    if MD_TABLE_ROW.search(text): errors.append('contains markdown table row')
    return errors
def validate_tables(text):
    errors=[]; rows=[line for line in text.splitlines() if line.strip().startswith('|') and line.strip().endswith('|')]
    if rows:
        if len(rows)>5: errors.append(f'table has too many rows: {len(rows)} > 5')
        max_cols=max(line.count('|')-1 for line in rows)
        if max_cols>3: errors.append(f'table has too many columns: {max_cols} > 3')
    return errors
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('message_plan_json'); ap.add_argument('--scripts-dir',default=None); ap.add_argument('--json-out'); args=ap.parse_args()
    plan_path=Path(args.message_plan_json); plan=json.loads(plan_path.read_text(encoding='utf-8'))
    errors=[]
    if plan.get('plain_text_only') is not True: errors.append('plain_text_only != true')
    if plan.get('no_large_tables') is not True: errors.append('no_large_tables != true')
    base=plan_path.parent
    for m in plan.get('messages',[]):
        p=Path(m.get('path',''))
        if not p.is_absolute(): p=base/p
        if not p.exists(): errors.append(f'missing message file: {p}'); continue
        text=p.read_text(encoding='utf-8',errors='replace')
        if len(text)>3900: errors.append(f'{p.name}: too long {len(text)} > 3900')
        for e in validate_plain(text): errors.append(f'{p.name}: {e}')
        for e in validate_tables(text): errors.append(f'{p.name}: {e}')
    result={'validated':not errors,'errors':errors,'message_count':len(plan.get('messages',[]))}
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors:
        print('\n'.join(errors),file=sys.stderr); return 1
    print('OK: telegram delivery validates'); return 0
if __name__=='__main__': raise SystemExit(main())
