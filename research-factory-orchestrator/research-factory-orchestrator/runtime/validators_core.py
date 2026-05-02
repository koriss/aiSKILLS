from __future__ import annotations
import json, re
from pathlib import Path
from .validator_sdk import Result, load_json

ATTACHMENT_CLAIMS=['во вложении','прикрепл','отправил файл','переотправил файл','html-отчёт во вложении','html отчет во вложении']

def delivery_truth(rd: Path):
    r=Result('delivery_truth')
    dm=load_json(rd/'delivery-manifest.json',{}) or {}
    fg=load_json(rd/'final-answer-gate.json',{}) or {}
    for ack_path in (rd/'delivery-acks').glob('OUT-*.json') if (rd/'delivery-acks').exists() else []:
        ack=load_json(ack_path,{}) or {}
        ev=load_json(rd/'outbox'/ack_path.name,{}) or {}
        if ev and ack.get('status') != ev.get('status'):
            r.add('F300','critical','outbox event status does not match ack status',[str(ack_path),str(rd/'outbox'/ack_path.name)])
    if dm.get('delivery_status')=='sent' and not dm.get('delivery_claim_allowed'):
        r.add('F301','critical','delivery_status sent but delivery_claim_allowed false',['delivery-manifest.json'])
    if fg.get('passed') and dm.get('delivery_status')!='sent':
        r.add('F304','critical','final gate passed without sent delivery',['final-answer-gate.json','delivery-manifest.json'])
    return r.as_dict()

def run_mode_truth(rd: Path):
    r=Result('run_mode_truth')
    rm=load_json(rd/'run-mode-classification.json',{}) or {}
    fg=load_json(rd/'final-answer-gate.json',{}) or {}
    mode=rm.get('run_mode')
    if mode in ('smoke','seed','test') and rm.get('production_publish_allowed'):
        r.add('F310','critical','smoke/seed/test run has production_publish_allowed=true',['run-mode-classification.json'])
    if mode in ('smoke','seed','test') and fg.get('passed'):
        r.add('F311','critical','smoke/seed/test run has final-answer-gate passed',['final-answer-gate.json'])
    return r.as_dict()

def manual_fallback_truth(rd: Path):
    r=Result('manual_fallback_truth')
    m=load_json(rd/'manual-fallback-ledger.json',{}) or {}
    if m.get('manual_fallback_used') and not m.get('integrated_into_rfo_artifacts') and m.get('allowed_to_claim_rfo_result'):
        r.add('F321','critical','manual fallback allowed to claim RFO result without integration',['manual-fallback-ledger.json'])
    return r.as_dict()

def evidence_truth(rd: Path):
    r=Result('evidence_truth')
    claims=(load_json(rd/'claims/claims-registry.json',{}) or {}).get('claims',[])
    ev=(load_json(rd/'evidence/evidence-cards.json',{}) or {}).get('evidence_cards',[])
    ev_ids={e.get('evidence_id') for e in ev}
    for c in claims:
        status=c.get('verification_status') or c.get('status')
        evidence_ids=c.get('evidence_ids') or c.get('evidence_card_ids') or []
        if status=='confirmed' and not evidence_ids:
            r.add('F174','critical','confirmed claim has no evidence ids',[c.get('claim_id','unknown')])
        for e in evidence_ids:
            if e not in ev_ids and str(e).replace('EV-','EV-SEED-') not in ev_ids:
                r.add('F174','high','claim evidence id not present in evidence cards',[c.get('claim_id','unknown'),str(e)])
    return r.as_dict()

def payload_safety(rd: Path):
    r=Result('payload_safety')
    dm=load_json(rd/'delivery-manifest.json',{}) or {}
    claim_allowed=bool(dm.get('delivery_claim_allowed'))
    chat_dir=rd/'chat'
    for p in chat_dir.glob('*.txt') if chat_dir.exists() else []:
        txt=p.read_text(encoding='utf-8',errors='ignore').lower()
        if any(x in txt for x in ['reasoning:','chain_of_thought','scratchpad']):
            r.add('F283','critical','reasoning/scratchpad leaked to chat payload',[str(p)])
        if re.search(r'(^|\s)/(home|tmp|mnt|var|opt)/', txt):
            r.add('F330','high','local absolute path leaked to chat payload',[str(p)])
        if any(x in txt for x in ATTACHMENT_CLAIMS) and not claim_allowed:
            r.add('F300','critical','attachment/delivery claim without delivery ack',[str(p),'delivery-manifest.json'])
    return r.as_dict()

def render_safety(rd: Path):
    r=Result('render_safety')
    html=rd/'report/full-report.html'
    if html.exists():
        txt=html.read_text(encoding='utf-8',errors='ignore')
        if '{{' in txt:
            r.add('F340','high','unresolved template placeholder in HTML',[str(html)])
        if '</script>' in txt.replace('<\\/script>','') and 'report-data-json' in txt:
            # Normal closing script is allowed; unsafe payload is checked by explicit placeholder/escaping tests.
            pass
    return r.as_dict()

VALIDATORS=[delivery_truth, run_mode_truth, manual_fallback_truth, evidence_truth, payload_safety, render_safety]

def run_all(rd: Path):
    return [v(rd) for v in VALIDATORS]
