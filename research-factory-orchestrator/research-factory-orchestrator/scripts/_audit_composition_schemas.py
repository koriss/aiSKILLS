#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SC=ROOT/'schemas'/'core'
REQ=['sources.schema.json','evidence-cards.schema.json','claims-registry.schema.json','final-answer-gate.schema.json','delivery-manifest.schema.json','contradictions-lite.schema.json','validation-transcript.schema.json']


def main()->int:
    errs=[]
    for n in REQ:
        p=SC/n
        if not p.is_file():
            errs.append(f'missing:{n}')
            continue
        try:
            o=json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            errs.append(f'parse:{n}:{e}')
            continue
        if o.get('$schema','').find('json-schema.org')<0:
            errs.append(f'bad_schema_decl:{n}')
        if o.get('type')!='object':
            errs.append(f'root_not_object:{n}')
    print(json.dumps({'status':'fail' if errs else 'pass','errors':errs},ensure_ascii=False,indent=2))
    return 1 if errs else 0

if __name__=='__main__':
    raise SystemExit(main())
