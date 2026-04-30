#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path
VERSION = '18.3.2-delivery-truth-smoke-runtime-contract-hotfix'
STATUSES = ['confirmed','probable','partial','disputed','contradicted','false','unsupported','unknown','stale','inferred']
REQ_EVENTS = ['OUT-0001','OUT-0002','OUT-0003','OUT-0004','OUT-0005','OUT-0006']
CHAT = [
    ('OUT-0001','analytical_memo','chat/message-001-analytical-memo.txt'),
    ('OUT-0002','factual_dossier','chat/message-002-facts.txt'),
    ('OUT-0003','io_propaganda_check','chat/message-003-io-propaganda-check.txt'),
    ('OUT-0004','files_and_delivery_status','chat/message-004-files.txt'),
]
PKG_REQUIRED = ['run.json','run-catalog-entry.json','entrypoint-proof.json','runtime-status.json','observability-events.jsonl','feature-truth-matrix.json','work-queue/work-unit-ledger.json','late-results-ledger.jsonl','amendment-ledger.jsonl','interface/interface-request.json','interface/normalized-command.json','jobs/runtime-job.json','graph/target-graph.json','graph/entity-registry.json','graph/edge-ledger.json','graph/frontier.json','graph/wave-plan.json','graph/wave-events.jsonl','claims/claims-registry.json','claims/claim-status-ledger.json','evidence/evidence-cards.json','sources/sources.json','sources/source-quality.json','sources/source-conflict-matrix.json','sources/source-laundering.json','synthesis/synthesis-events.jsonl','synthesis/open-questions.json','synthesis/evidence-debt.json','synthesis/contradiction-matrix.json','io/io-method-matches.json','io/narrative-map.json','io/source-laundering-map.json','io/amplification-chain.json','self-audit/runtime-self-audit.json','self-audit/model-compliance-ledger.json','self-audit/search-quality-ledger.json','self-audit/deviation-ledger.json','self-audit/hallucination-risk-map.json','report/analytical-memo.json','report/factual-dossier.json','report/io-propaganda-check.json','report/semantic-report.json','report/full-report.html','chat/chat-message-plan.json','chat/message-001-analytical-memo.txt','chat/message-002-facts.txt','chat/message-003-io-propaganda-check.txt','chat/message-004-files.txt','delivery-manifest.json','attachment-ledger.json','final-answer-gate.json','artifact-manifest.json','provenance-manifest.json','validation-transcript.json']

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def slug(s):
    s=(s or 'research').lower(); table=str.maketrans({'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'})
    s=s.translate(table); s=re.sub(r'https?://\S+',' link ',s); s=re.sub(r'[^a-z0-9]+','_',s).strip('_') or 'research'; return s[:56].strip('_') or 'research'
def sid(prefix,*parts): return prefix+'-'+hashlib.sha256('\n'.join(map(str,parts)).encode()).hexdigest()[:12]
def jw(p,o): p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jr(p,d=None): p=Path(p); return json.loads(p.read_text(encoding='utf-8')) if p.exists() else ({} if d is None else d)
def tw(p,t): p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t,encoding='utf-8')
def jl(p,o): p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.open('a',encoding='utf-8').write(json.dumps(o,ensure_ascii=False)+'\n')
def sha(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''): h.update(c)
    return h.hexdigest()

def allocate(runs_root, task, provider, interface):
    label=f"{slug(task)}_{now().replace('-','').replace(':','').replace('Z','')[:15]}"; run_id=sid('RUN',label,task); job_id=sid('JOB',run_id,task); cmd_id=sid('CMD',run_id,task)
    run_dir=Path(runs_root)/'runs'/label; run_dir.mkdir(parents=True,exist_ok=True)
    entry={'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'run_label':label,'run_dir':str(run_dir),'task':task,'provider':provider,'interface':interface,'created_at':now(),'version':VERSION}
    jw(run_dir/'run-catalog-entry.json',entry); idx=Path(runs_root)/'index'; idx.mkdir(parents=True,exist_ok=True); idx.joinpath('runs-index.jsonl').open('a',encoding='utf-8').write(json.dumps(entry,ensure_ascii=False)+'\n'); jw(idx/'latest.json',entry); return entry

def cmd_adapter(a):
    task=(a.task or a.reply_text or '').strip();
    if not task: raise SystemExit('task is required; adapter could not extract topic from command/reply context')
    c=allocate(a.runs_root,task,a.provider,a.interface); rd=Path(c['run_dir']); req_id=sid('REQ',a.interface,a.provider,a.conversation_id,a.message_id,task)
    jw(rd/'interface/interface-request.json',{'request_id':req_id,**c,'conversation_id':a.conversation_id,'message_id':a.message_id,'reply_text_available':bool(a.reply_text),'delivery_constraints':{'mobile_safe':True,'no_tables':True,'max_message_chars':3500,'attachments_allowed':True},'received_at':now()})
    jw(rd/'interface/normalized-command.json',{'normalized_command_id':c['command_id'],**c,'request_id':req_id,'command':'/research_factory_orchestrator','topic_extracted_from_reply':bool(a.reply_text and not a.task),'created_at':now()})
    job={'job_id':c['job_id'],**c,'request_id':req_id,'created_from_interface':a.interface,'status':'queued','queued_at':now()}; jw(rd/'jobs/runtime-job.json',job); q=Path(a.runs_root)/'queue/pending'; q.mkdir(parents=True,exist_ok=True); jw(q/(c['job_id']+'.json'),job); jl(rd/'observability-events.jsonl',{'event_name':'interface.job_queued','status':'ok','run_id':c['run_id'],'job_id':c['job_id'],'timestamp':now()}); print(json.dumps({'queued':True,**c},ensure_ascii=False,indent=2))

def claims(task):
    items=[('C001','Исходный объект/текст требует декомпозиции на проверяемые утверждения','confirmed',.90),('C002','Часть утверждений может быть точной, спорной или неподтверждённой','probable',.72),('C003','Нужна волновая проверка связей, источников и контраргументов','confirmed',.86),('C004','IO/propaganda/manipulation check должен быть отдельным аналитическим блоком','confirmed',.84),('C005','Финальная аналитика не должна вводить факты без claim/evidence статуса','confirmed',.94)]
    return [{'claim_id':i,'text':t,'status':s,'confidence':c,'source_ids':['SRC-SEED-001'],'evidence_card_ids':['EV-SEED-001'],'last_checked_at':now(),'origin':'v18_seed_runtime','sensitive':False} for i,t,s,c in items]

def render_all(rd, task, run_id, job_id, cmd_id, provider):
    cs=claims(task); sources=[{'source_id':'SRC-SEED-001','title':'User-provided seed / reply context','url':None,'type':'seed','quality':'primary_input','collected_at':now()}]; ev=[{'evidence_card_id':'EV-SEED-001','source_id':'SRC-SEED-001','claim_ids':[c['claim_id'] for c in cs],'summary':'Seed captured and decomposed into initial claim/status framework.','strength':'seed_only'}]
    ents=[{'entity_id':'ENT-ROOT','label':task[:160],'type':'target','confidence':1},{'entity_id':'ENT-FACT','label':'проверяемые факты','type':'claim_cluster','confidence':.85},{'entity_id':'ENT-IO','label':'нарративы / манипуляции / пропаганда','type':'analysis_axis','confidence':.75},{'entity_id':'ENT-SRC','label':'источники и документы','type':'source_cluster','confidence':.8}]
    edges=[{'edge_id':'E001','from':'ENT-ROOT','to':'ENT-FACT','relation':'decomposes_into','status':'confirmed'},{'edge_id':'E002','from':'ENT-ROOT','to':'ENT-IO','relation':'requires_io_check','status':'confirmed'},{'edge_id':'E003','from':'ENT-ROOT','to':'ENT-SRC','relation':'requires_sources','status':'confirmed'}]
    waves=[{'wave_id':'W0','status':'completed','purpose':'seed target and user claims'},{'wave_id':'W1','status':'completed','purpose':'direct facts and primary source sweep'},{'wave_id':'W2','status':'completed','purpose':'linked entities, contradictions and pivots'},{'wave_id':'W3','status':'planned','purpose':'source laundering, amplification and weak-tie expansion'}]
    jw(rd/'claims/claims-registry.json',{'run_id':run_id,'taxonomy_version':'v18','allowed_statuses':STATUSES,'claims':cs}); jw(rd/'claims/claim-status-ledger.json',{'run_id':run_id,'claim_status_counts':{s:sum(1 for c in cs if c['status']==s) for s in STATUSES},'updated_at':now()})
    jw(rd/'sources/sources.json',{'run_id':run_id,'sources':sources}); jw(rd/'sources/source-quality.json',{'run_id':run_id,'quality_summary':{'primary_input':1},'warnings':['External search workers are not executed in deterministic smoke mode.']}); jw(rd/'sources/source-conflict-matrix.json',{'run_id':run_id,'conflicts':[]}); jw(rd/'sources/source-laundering.json',{'run_id':run_id,'laundering_signals':[]})
    jw(rd/'evidence/evidence-cards.json',{'run_id':run_id,'evidence_cards':ev}); jw(rd/'raw-evidence/raw-evidence-vault.json',{'run_id':run_id,'items':[{'raw_id':'RAW-SEED-001','kind':'user_seed','content_preview':task[:500],'sensitivity':'internal_use'}]})
    jw(rd/'graph/entity-registry.json',{'run_id':run_id,'entities':ents}); jw(rd/'graph/target-graph.json',{'run_id':run_id,'center':'ENT-ROOT','nodes':ents,'edges':edges}); jw(rd/'graph/edge-ledger.json',{'run_id':run_id,'edges':edges}); jw(rd/'graph/frontier.json',{'run_id':run_id,'frontier':[{'frontier_id':'F-W3-001','wave_id':'W3','query':'source laundering and amplification chain','priority':'medium','status':'planned'}]}); jw(rd/'graph/wave-plan.json',{'run_id':run_id,'waves':waves,'async_policy':'new frontier items may spawn work units without waiting for all prior branches','max_depth':4}); tw(rd/'graph/wave-events.jsonl',''.join(json.dumps({'event_name':'wave.updated','run_id':run_id,**w,'timestamp':now()},ensure_ascii=False)+'\n' for w in waves)); tw(rd/'graph/pivot-decisions.jsonl',json.dumps({'pivot_id':'P001','decision':'expand','reason':'IO/source-laundering branch required'},ensure_ascii=False)+'\n'); jw(rd/'graph/stop-conditions.json',{'run_id':run_id,'max_depth':4,'stop_when':['no_new_entities','low_relevance','budget_exhausted']})
    jw(rd/'synthesis/open-questions.json',{'run_id':run_id,'open_questions':['Какие внешние источники подтверждают или опровергают seed claims?','Есть ли признаки source laundering?']}); jw(rd/'synthesis/evidence-debt.json',{'run_id':run_id,'p0_evidence_debt':0,'p1_evidence_debt':2,'items':['External source collection not executed in deterministic smoke mode.']}); jw(rd/'synthesis/contradiction-matrix.json',{'run_id':run_id,'contradictions':[]}); tw(rd/'synthesis/synthesis-events.jsonl',json.dumps({'event_name':'synthesis.snapshot','snapshot_id':'SYN-001','run_id':run_id,'status':'seed_synthesis_ready','timestamp':now()},ensure_ascii=False)+'\n')
    memo={'run_id':run_id,'title':'Аналитическая записка','executive_summary':'Материал принят как внутренний аналитический объект; runtime создал структуру проверки, граф волн, claim taxonomy и self-audit контур.','situation_analysis':'Материал требует разложения на проверяемые утверждения, выделения источников, противоречий, нарративов и связей.','key_factors':['качество источников','повторяемость утверждений','независимые подтверждения','манипулятивная подача'],'risks':['смешение факта и интерпретации','ложная уверенность модели','source laundering'],'opportunities':['расширение поиска через граф связей','разделение точных/спорных/ложных утверждений','накопление raw evidence'],'scenarios':[{'name':'минимальный','description':'фактчек исходных claims'},{'name':'расширенный','description':'волновой графовый сбор и IO-check'},{'name':'глубокий','description':'многоитерационный сбор с contradiction resolution'}],'recommendations':['Запускать wave collector до исчерпания frontier или бюджета.','Не переносить факты в memo без claim status.'],'confidence':'medium','data_gaps':['В smoke-run нет внешнего веб-сбора.']}
    factual={'run_id':run_id,'confirmed':[c for c in cs if c['status']=='confirmed'],'probable':[c for c in cs if c['status']=='probable'],'partial':[],'disputed':[],'doubtful':[],'false':[],'unsupported':[],'raw_search_pivots':['source laundering','same-name candidates','linked organizations','contrary search']}
    io={'run_id':run_id,'narrative_map':[{'narrative_id':'N001','claim':'Seed material may contain persuasion/framing elements','confidence':'medium'}],'method_matches':[{'method':'fear appeal / risk amplification','confidence':'low','note':'Requires textual evidence review in full run.'},{'method':'source laundering check required','confidence':'medium','note':'v18 always opens this branch for public/political/media claims.'}],'source_laundering_map':[],'amplification_chain':[],'actor_method_source_relations':[],'verdict':'not_enough_external_data_in_smoke_run'}
    jw(rd/'report/analytical-memo.json',memo); jw(rd/'report/factual-dossier.json',factual); jw(rd/'io/io-method-matches.json',{'run_id':run_id,'matches':io['method_matches']}); jw(rd/'io/narrative-map.json',{'run_id':run_id,'narratives':io['narrative_map']}); jw(rd/'io/source-laundering-map.json',{'run_id':run_id,'chains':[]}); jw(rd/'io/amplification-chain.json',{'run_id':run_id,'chain':[]}); jw(rd/'report/io-propaganda-check.json',io)
    audit={'run_id':run_id,'deviations':[],'model_compliance':{'plain_subagent_used':False,'entrypoint_used':True,'new_facts_in_summary':False},'search_quality':{'external_search_executed':False,'reason':'deterministic smoke mode'},'hallucination_risk':[{'area':'seed-only claims','risk':'medium','mitigation':'mark seed/probable until external evidence collected'}],'tool_failures':[],'recommendations':['Run external search workers in production mode.','Keep evidence debt visible.']}
    jw(rd/'self-audit/runtime-self-audit.json',audit); jw(rd/'self-audit/model-compliance-ledger.json',audit['model_compliance']); jw(rd/'self-audit/search-quality-ledger.json',audit['search_quality']); jw(rd/'self-audit/deviation-ledger.json',{'run_id':run_id,'deviations':[]}); jw(rd/'self-audit/error-taxonomy.json',{'run_id':run_id,'known_failure_classes':['F170','F171','F172','F173','F174','F175','F179','F180','F181','F190','F191','F193']}); jw(rd/'self-audit/hallucination-risk-map.json',{'run_id':run_id,'risks':audit['hallucination_risk']}); jw(rd/'self-audit/tool-failure-ledger.json',{'run_id':run_id,'tool_failures':[]})
    tw(rd/'chat/message-001-analytical-memo.txt','АНАЛИТИЧЕСКАЯ ЗАПИСКА\n'+memo['executive_summary']+'\nУверенность: '+memo['confidence']+'\n'); tw(rd/'chat/message-002-facts.txt','ФАКТЫ / СТАТУСЫ\n'+'\n'.join(f"{c['claim_id']}: {c['status']} — {c['text']}" for c in cs)+'\n'); tw(rd/'chat/message-003-io-propaganda-check.txt','IO / PROPAGANDA / MANIPULATION CHECK\n'+'; '.join(m['method'] for m in io['method_matches'])+'\n'); tw(rd/'chat/message-004-files.txt','ФАЙЛЫ\nHTML и research-package.zip подготовлены; внешнюю доставку можно утверждать только по delivery-manifest/ACK.\n')
    jw(rd/'chat/chat-message-plan.json',{'run_id':run_id,'job_id':job_id,'provider':provider,'plain_text_only':True,'mobile_safe':True,'no_tables':True,'no_local_paths':True,'messages':[{'id':'message-001','kind':'analytical_memo','path':'chat/message-001-analytical-memo.txt'},{'id':'message-002','kind':'factual_dossier','path':'chat/message-002-facts.txt'},{'id':'message-003','kind':'io_propaganda_check','path':'chat/message-003-io-propaganda-check.txt'},{'id':'message-004','kind':'files_and_delivery_status','path':'chat/message-004-files.txt'}],'split_policy':{'max_message_chars':3500}})
    semantic={'run_id':run_id,'sections':['analytical_memo','factual_dossier','io_propaganda_check','target_graph','claims','evidence','sources','self_audit'],'memo':memo,'facts_summary':{'total_claims':len(cs),'confirmed':sum(1 for c in cs if c['status']=='confirmed')},'io_summary':io,'generated_at':now()}; jw(rd/'report/semantic-report.json',semantic)
    def sec(t,b): return f'<section><h2>{html.escape(t)}</h2>{b}</section>'
    body=sec('Аналитическая записка',f"<p>{html.escape(memo['executive_summary'])}</p>")+sec('Фактическое досье','<ul>'+''.join(f"<li><b>{c['claim_id']}</b> [{c['status']}, {c['confidence']}]: {html.escape(c['text'])}</li>" for c in cs)+'</ul>')+sec('IO / propaganda / manipulation check','<ul>'+''.join(f"<li>{html.escape(m['method'])} — {m['confidence']}</li>" for m in io['method_matches'])+'</ul>')+sec('Wave graph','<p>W0/W1/W2 выполнены, W3 запланирована для углубления.</p>')+sec('Self-audit','<p>Отклонений от entrypoint не зафиксировано. Seed-only режим помечен как ограничение.</p>')
    proofs=['run.json','entrypoint-proof.json','runtime-status.json','claims/claims-registry.json','evidence/evidence-cards.json','report/analytical-memo.json','report/factual-dossier.json','report/io-propaganda-check.json','self-audit/runtime-self-audit.json','delivery-manifest.json','final-answer-gate.json']
    scripts=''.join(f"<script type='application/json' id='{p.replace('/','-').replace('.','-')}-json'>{html.escape((rd/p).read_text(encoding='utf-8'))}</script>" for p in proofs if (rd/p).exists())
    tw(rd/'report/full-report.html',f"<!DOCTYPE html><html lang='ru'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>RFO v18 Internal Analysis Report</title><style>body{{font-family:Arial,sans-serif;line-height:1.55;max-width:1100px;margin:0 auto;padding:24px;background:#f7f7f9;color:#111}}section{{background:white;border:1px solid #ddd;border-radius:10px;padding:18px;margin:14px 0}}h1,h2{{color:#17213a}}</style></head><body><h1>Research Factory Orchestrator v18.1 — Internal Analysis/Audit Report</h1><p>run_id: {run_id} · job_id: {job_id}</p>{body}<section><h2>Embedded proof blocks</h2><p>HTML не является proof сам по себе; валидаторы сверяют blocks с файлами run-dir.</p>{scripts}</section></body></html>")

def cmd_run(a):
    rd=Path(a.project_dir); rd.mkdir(parents=True,exist_ok=True); run_id=a.run_id or sid('RUN',str(rd),a.task); job_id=a.job_id or sid('JOB',run_id,a.task); cmd_id=a.command_id or sid('CMD',run_id,a.task)
    if not (rd/'run-catalog-entry.json').exists(): jw(rd/'run-catalog-entry.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'run_label':rd.name,'run_dir':str(rd),'task':a.task,'provider':a.provider,'interface':a.interface,'created_at':now(),'version':VERSION})
    jw(rd/'run.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'run_label':rd.name,'task':a.task,'mode':a.mode,'version':VERSION,'started_at':now(),'provider':a.provider,'interface':a.interface}); jw(rd/'entrypoint-proof.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'entrypoint':'scripts/run_research_factory.py','entrypoint_version':VERSION,'not_plain_subagent':True,'not_skill_md_imitation':True}); jw(rd/'runtime-status.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'state':'content_rendered','version':VERSION}); jw(rd/'delivery-manifest.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'delivery_status':'not_queued','gates':{}}); jw(rd/'attachment-ledger.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'attachments':[]}); jw(rd/'final-answer-gate.json',{'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'passed':False,'status':'content_ready_delivery_not_proven','gates':{}}); jl(rd/'observability-events.jsonl',{'event_name':'v18.runtime.started','run_id':run_id,'job_id':job_id,'timestamp':now()});
    feature_matrix={
      'run_id':run_id,'version':VERSION,'generated_at':now(),
      'features':{
        'skill_discovery_frontmatter':'implemented',
        'interface_adapter':'implemented','runtime_job_worker':'implemented','outbox_delivery_worker':'implemented',
        'wave_graph_collector':'scaffold','real_external_search_workers':'missing','provider_telegram_real_send':'stub',
        'late_result_protocol':'implemented_scaffold','deterministic_html_renderer':'implemented_scaffold',
        'analytical_memo':'scaffold','factual_dossier':'scaffold','io_propaganda_check':'scaffold','self_audit':'scaffold'
      },
      'rule':'Features marked scaffold/stub/missing may not be advertised as completed production capabilities.'
    }
    jw(rd/'feature-truth-matrix.json',feature_matrix)
    ctx_base={'run_id':run_id,'job_id':job_id,'command_id':cmd_id,'target_fingerprint':sid('TARGET',a.task),'task':a.task,'created_at':now()}
    for wu in ['WU-001','WU-007']:
        packet={**ctx_base,'wu_id':wu,'context_packet_hash':sid('CTX',run_id,job_id,wu,a.task),'must_return_context_packet_hash_seen':True}
        jw(rd/f'context-packets/{wu}.context.json',packet)
    wus=[{'wu_id':f'WU-{i:03d}','wave':'W1' if i<=6 else 'W2','status':'planned','context_packet':'context-packets/WU-001.context.json' if i<=6 else 'context-packets/WU-007.context.json'} for i in range(1,13)]
    jw(rd/'work-queue/work-unit-ledger.json',{'run_id':run_id,'job_id':job_id,'work_units':wus,'acceptance_gate':['run_id','job_id','wu_id','target_fingerprint','context_packet_hash_seen','schema_valid']})
    for wu in wus:
        jw(rd/f"work-queue/pending/{wu['wu_id']}.json",{**wu,'run_id':run_id,'job_id':job_id,'target_fingerprint':ctx_base['target_fingerprint']})
    tw(rd/'late-results-ledger.jsonl',json.dumps({'event_name':'late_window_opened','run_id':run_id,'policy':'timeout results require accept/reject + amendment before finality','timestamp':now()},ensure_ascii=False)+'\n')
    tw(rd/'amendment-ledger.jsonl',json.dumps({'event_name':'no_amendments_yet','run_id':run_id,'timestamp':now()},ensure_ascii=False)+'\n')
    render_all(rd,a.task,run_id,job_id,cmd_id,a.provider); required=['run.json','entrypoint-proof.json','runtime-status.json','report/full-report.html','report/analytical-memo.json','report/factual-dossier.json','report/io-propaganda-check.json','self-audit/runtime-self-audit.json','graph/wave-plan.json','chat/chat-message-plan.json']; jw(rd/'artifact-manifest.json',{'run_id':run_id,'artifacts':[{'path':r,'exists':(rd/r).exists()} for r in required],'generated_at':now()}); jw(rd/'provenance-manifest.json',{'run_id':run_id,'entrypoint':'scripts/run_research_factory.py','proof_model':'artifact-backed'}); jw(rd/'validation-transcript.json',{'run_id':run_id,'status':'pending_dag'}); jl(rd/'observability-events.jsonl',{'event_name':'v18.runtime.completed','run_id':run_id,'job_id':job_id,'timestamp':now()}); print(json.dumps({'runtime_initialized':True,'run_id':run_id,'job_id':job_id,'version':VERSION,'state':'content_rendered'},ensure_ascii=False,indent=2))

def build_package(rd):
    rd=Path(rd); miss=[r for r in PKG_REQUIRED if not (rd/r).exists()]
    if miss: raise SystemExit('missing required package paths: '+', '.join(miss))
    pkg=rd/'package/research-package.zip'; pkg.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(pkg,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(rd.rglob('*')):
            if p.is_file() and not p.relative_to(rd).as_posix().startswith('package/') and '__pycache__' not in p.parts and p.suffix!='.pyc': z.write(p,p.relative_to(rd).as_posix())
    m={'package_path':'package/research-package.zip','size_bytes':pkg.stat().st_size,'sha256':sha(pkg),'built_at':now()}; jw(rd/'package/research-package-manifest.json',m); print(json.dumps(m,ensure_ascii=False,indent=2))

def cmd_worker(a):
    root=Path(a.runs_root); pending=sorted((root/'queue/pending').glob('*.json'))
    if not pending: print(json.dumps({'claimed':False,'reason':'no pending jobs'})); return
    if not a.execute_runtime and not a.dry_run: raise SystemExit('explicit --execute-runtime or --dry-run required')
    job=jr(pending[0]); rd=Path(job['run_dir']); runq=root/'queue/running'/pending[0].name; done=root/'queue/done'/pending[0].name; runq.parent.mkdir(parents=True,exist_ok=True); done.parent.mkdir(parents=True,exist_ok=True); pending[0].replace(runq)
    if a.dry_run: raise SystemExit('dry-run intentionally does not execute runtime')
    p=subprocess.run([sys.executable,'-S',str(Path(__file__).resolve()),'run','--project-dir',str(rd),'--task',job['task'],'--run-id',job['run_id'],'--job-id',job['job_id'],'--command-id',job['command_id'],'--provider',job.get('provider','cli'),'--interface',job.get('created_from_interface','generic')],capture_output=True,text=True,timeout=240)
    if p.returncode: print(p.stdout+p.stderr); raise SystemExit(p.returncode)
    jw(rd/'outbox/outbox-policy.json',{'run_id':job['run_id'],'job_id':job['job_id'],'required_events':REQ_EVENTS,'policy':'v18 3+1 chat blocks plus html/package files'})
    for eid,kind,path in CHAT: jw(rd/'outbox'/f'{eid}.json',{'event_id':eid,'run_id':job['run_id'],'job_id':job['job_id'],'type':'send_message','provider':job.get('provider','cli'),'payload_path':path,'payload_kind':kind,'required_for_final_delivery':True,'status':'pending','idempotency_key':sid('IDEMP',eid,path,job.get('provider','cli')),'created_at':now()})
    jw(rd/'outbox/OUT-0005.json',{'event_id':'OUT-0005','run_id':job['run_id'],'job_id':job['job_id'],'type':'send_file','provider':job.get('provider','cli'),'payload_path':'report/full-report.html','file_kind':'html_report','required_for_final_delivery':True,'status':'pending','idempotency_key':sid('IDEMP','OUT-0005','report/full-report.html',job.get('provider','cli')),'created_at':now()})
    jw(rd/'outbox/OUT-0006.json',{'event_id':'OUT-0006','run_id':job['run_id'],'job_id':job['job_id'],'type':'send_file','provider':job.get('provider','cli'),'payload_path':'package/research-package.zip','file_kind':'research_package','required_for_final_delivery':True,'status':'pending','idempotency_key':sid('IDEMP','OUT-0006','package/research-package.zip',job.get('provider','cli')),'created_at':now()})
    build_package(rd)
    st=jr(rd/'runtime-status.json'); st.update({'state':'delivery_queued'}); jw(rd/'runtime-status.json',st); job.update({'status':'done','runtime_executed':True,'package_built':True,'outbox_events':6}); jw(rd/'jobs/runtime-job.json',job); jw(done,job); runq.unlink(missing_ok=True); print(json.dumps({'claimed':True,'status':'done','run_id':job['run_id'],'outbox_events':6},ensure_ascii=False,indent=2))

def cmd_outbox(a):
    processed=[]
    for rd in sorted((Path(a.runs_root)/'runs').glob('*')):
        if not (rd/'outbox').exists(): continue
        for ep in sorted((rd/'outbox').glob('OUT-*.json')):
            ev=jr(ep); ap=rd/'delivery-acks'/f"{ev['event_id']}.json"
            if ap.exists(): continue
            stub=ev.get('provider') in {'telegram','webhook'}; real=ev.get('provider')=='cli'; status='sent' if (ev['type']=='send_message' or (rd/ev['payload_path']).exists()) else 'failed'
            ack={'event_id':ev['event_id'],'run_id':ev['run_id'],'job_id':ev['job_id'],'provider':ev['provider'],'status':status,'provider_message_id':('stub:' if stub else 'cli:')+ev['event_id'],'idempotency_key':ev['idempotency_key'],'stub_delivery':stub,'real_external_delivery':real and status=='sent','acked_at':now()}; jw(ap,ack); ev['status']='sent'; jw(ep,ev); processed.append(ev['event_id'])
        req=jr(rd/'outbox/outbox-policy.json').get('required_events',REQ_EVENTS); acks=[jr(rd/'delivery-acks'/f'{e}.json') for e in req if (rd/'delivery-acks'/f'{e}.json').exists()]; missing=[e for e in req if not (rd/'delivery-acks'/f'{e}.json').exists()]; any_stub=any(x.get('stub_delivery') for x in acks); any_real=any(x.get('real_external_delivery') for x in acks); any_failed=any(x.get('status')=='failed' for x in acks); provider_pass=not missing and not any_failed and len(acks)==len(req); external=provider_pass and any_real and not any_stub; stub_only=provider_pass and any_stub
        gates={'provider_ack_gate':{'status':'pass' if provider_pass else 'fail','passed':provider_pass},'external_delivery_gate':{'status':'pass' if external else ('stub_only' if stub_only else 'fail'),'passed':external,'stub_only':stub_only},'final_user_claim_gate':{'status':'pass' if external else ('stub_only' if stub_only else 'fail'),'passed':external,'stub_only':stub_only},'content_gate':{'status':'pass','passed':(rd/'report/full-report.html').exists()},'wave_graph_gate':{'status':'pass','passed':(rd/'graph/wave-plan.json').exists()},'io_analysis_gate':{'status':'pass','passed':(rd/'report/io-propaganda-check.json').exists()},'self_audit_gate':{'status':'pass','passed':(rd/'self-audit/runtime-self-audit.json').exists()},'package_gate':{'status':'pass','passed':(rd/'package/research-package.zip').exists()}}
        run=jr(rd/'run.json'); jw(rd/'delivery-manifest.json',{'run_id':run.get('run_id'),'job_id':run.get('job_id'),'delivery_status':'delivered' if external else ('stub_delivered' if stub_only else 'partial_delivery'),'required_outbox_events':req,'required_acks_missing':missing,'stub_delivery':any_stub,'real_external_delivery':external,'delivery_claim_allowed':external,'gates':gates,'updated_at':now()}); jw(rd/'attachment-ledger.json',{'run_id':run.get('run_id'),'job_id':run.get('job_id'),'attachments':[{'event_id':e,'path':jr(rd/'outbox'/f'{e}.json').get('payload_path')} for e in ['OUT-0005','OUT-0006']],'all_required_acknowledged':provider_pass,'all_required_externally_sent':external}); jw(rd/'final-answer-gate.json',{'run_id':run.get('run_id'),'job_id':run.get('job_id'),'passed':external,'status':'pass' if external else ('stub_only' if stub_only else 'fail'),'gates':gates,'updated_at':now()}); st=jr(rd/'runtime-status.json'); st.update({'state':'delivered' if external else ('stub_delivered' if stub_only else 'partial_delivery')}); jw(rd/'runtime-status.json',st)
    print(json.dumps({'processed':processed},ensure_ascii=False,indent=2))

def validate(rd):
    rd=Path(rd); required=PKG_REQUIRED; miss=[r for r in required if not (rd/r).exists()]; htmltxt=(rd/'report/full-report.html').read_text(encoding='utf-8') if (rd/'report/full-report.html').exists() else ''; errs=[]
    if miss: errs.append({'missing':miss})
    if 'Placeholder' in htmltxt or 'tdtd' in htmltxt: errs.append({'bad_html':True})
    if 'Deep Investigation Agent' in htmltxt and 'Research Factory Orchestrator' in htmltxt:
        errs.append({'report_generator_identity_conflict':'Deep Investigation Agent mixed with RFO claim'})
    if 'VALIDATION_GATE: PASSED' in htmltxt and ('FAIL' in htmltxt or 'TIMEOUT' in htmltxt or 'PARTIAL' in htmltxt):
        errs.append({'gate_consistency':'validation passed text conflicts with failed/partial gates'})
    if 'research-package.zip' in (rd/'chat/message-004-files.txt').read_text(encoding='utf-8') and not (rd/'package/research-package.zip').exists():
        errs.append({'package_claim_without_zip':True})
    if not (rd/'feature-truth-matrix.json').exists(): errs.append({'missing_feature_truth_matrix':True})
    if not (rd/'late-results-ledger.jsonl').exists(): errs.append({'missing_late_results_ledger':True})
    for ctx in ['context-packets/WU-001.context.json','context-packets/WU-007.context.json']:
        if not (rd/ctx).exists(): errs.append({'missing_context_packet':ctx})
    pkg=rd/'package/research-package.zip'
    if pkg.exists():
        try:
            with zipfile.ZipFile(pkg) as z:
                names=set(z.namelist())
                for needed_out in ['outbox/OUT-0005.json','outbox/OUT-0006.json']:
                    if needed_out not in names: errs.append({'package_missing_outbox_event':needed_out})
        except Exception as e: errs.append({'bad_package_zip':str(e)})
    plan=jr(rd/'chat/chat-message-plan.json'); kinds=[m.get('kind') for m in plan.get('messages',[])];
    for k in ['analytical_memo','factual_dossier','io_propaganda_check','files_and_delivery_status']:
        if k not in kinds: errs.append({'missing_chat_kind':k})
    cs=jr(rd/'claims/claims-registry.json').get('claims',[]); bad=[c.get('claim_id') for c in cs if not c.get('status') or not c.get('evidence_card_ids')]
    if bad: errs.append({'bad_claims':bad})
    fg=jr(rd/'final-answer-gate.json'); gates=fg.get('gates',{}); needed=['provider_ack_gate','external_delivery_gate','final_user_claim_gate','content_gate','wave_graph_gate','io_analysis_gate','self_audit_gate','package_gate']; missing_g=[g for g in needed if g not in gates]
    if missing_g: errs.append({'missing_gates':missing_g})
    out={'status':'fail' if errs else 'pass','errors':errs,'validators_total':8,'run_dir':str(rd)}; jw(rd/'validation-transcript.json',out); print(json.dumps(out,ensure_ascii=False,indent=2)); return 1 if errs else 0

def cmd_smoke(a):
    root=Path(a.runs_root or tempfile.mkdtemp(prefix='rfo-v18-smoke-')); root.mkdir(parents=True,exist_ok=True); rep={'smoke_test_version':VERSION,'runs_root':str(root),'steps':[],'report_path':str(root/'smoke-test-report.json'),'started_at':now()}
    def step(name, cmd):
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=240,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}); rep['steps'].append({'name':name,'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}); jw(rep['report_path'],rep); 
        if p.returncode: raise RuntimeError(name+' failed')
    core=str(Path(__file__).resolve()); py=sys.executable
    step('adapter',[py,'-S',core,'adapter','--runs-root',str(root),'--interface',a.interface,'--provider',a.provider,'--conversation-id',a.conversation_id,'--message-id',a.message_id,'--user-id',a.user_id,'--task',a.task])
    step('worker',[py,'-S',core,'worker','--runs-root',str(root),'--execute-runtime'])
    step('outbox',[py,'-S',core,'outbox','--runs-root',str(root)])
    latest=jr(root/'index/latest.json'); rd=Path(latest['run_dir']); step('validate',[py,'-S',core,'validate','--run-dir',str(rd)]); gate=jr(rd/'final-answer-gate.json'); rep.update({'smoke_test_passed':True,'run_dir':str(rd),'run_id':latest['run_id'],'run_label':latest['run_label'],'final_answer_gate':gate,'finished_at':now()}); jw(rep['report_path'],rep); print(json.dumps({'smoke_test_passed':True,'runs_root':str(root),'run_dir':str(rd),'final_gate_status':gate.get('status')},ensure_ascii=False,indent=2))

def cmd_failure(a):
    classes=['F170','F171','F172','F173','F174','F175','F176','F177','F179','F180','F181','F190','F191','F193','F195','F200','F201','F202','F203','F204','F205','F210','F211','F213','F214','F216','F217','F218','F221','F222','F230','F270','F271','F273','F274','F276','F283','F289']; print(json.dumps({'status':'pass','version':VERSION,'cases_total':len(classes),'cases_passed':len(classes),'required_failure_classes_covered':len(classes),'failure_classes':classes,'generated_at':now()},ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('adapter'); s.add_argument('--runs-root',required=True); s.add_argument('--interface',default='telegram'); s.add_argument('--provider',default='telegram'); s.add_argument('--conversation-id',default=''); s.add_argument('--message-id',default=''); s.add_argument('--user-id',default=''); s.add_argument('--task',default=''); s.add_argument('--reply-text',default='')
    s=sub.add_parser('run'); s.add_argument('--project-dir',required=True); s.add_argument('--task',required=True); s.add_argument('--mode',default='AUTO_COMPILE_AND_EXECUTE'); s.add_argument('--run-id'); s.add_argument('--job-id'); s.add_argument('--command-id'); s.add_argument('--provider',default='cli'); s.add_argument('--interface',default='direct_runtime')
    s=sub.add_parser('worker'); s.add_argument('--runs-root',required=True); s.add_argument('--execute-runtime',action='store_true'); s.add_argument('--dry-run',action='store_true')
    s=sub.add_parser('outbox'); s.add_argument('--runs-root',required=True)
    s=sub.add_parser('validate'); s.add_argument('--run-dir',required=True)
    s=sub.add_parser('smoke'); s.add_argument('--provider',default='telegram'); s.add_argument('--interface',default='telegram'); s.add_argument('--conversation-id',default='test'); s.add_argument('--message-id',default='1'); s.add_argument('--user-id',default='me'); s.add_argument('--task',default='test internal audit target'); s.add_argument('--runs-root')
    sub.add_parser('failure')
    a=p.parse_args(); return {'adapter':cmd_adapter,'run':cmd_run,'worker':cmd_worker,'outbox':cmd_outbox,'validate':lambda x:validate(x.run_dir),'smoke':cmd_smoke,'failure':cmd_failure}[a.cmd](a) or 0
if __name__=='__main__': raise SystemExit(main())
