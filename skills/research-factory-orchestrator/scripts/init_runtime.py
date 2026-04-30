#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json
from common_runtime import VERSION, AXES, SOURCE_FAMILIES, now, slugify, jwrite, twrite, event, jread

def make_work_units():
    units=[]
    for i, axis in enumerate(AXES, 1):
        collection = axis not in ["synthesis_merge", "raw_evidence_vault"]
        units.append({
            "work_unit_id": f"WU-{i:03d}-{axis.replace('_','-')}",
            "axis": axis,
            "objective": f"Execute {axis} coverage for the target task.",
            "status": "planned",
            "collection_unit": collection,
            "minimum_queries": 3 if collection else 0,
            "minimum_sources": 2 if collection else 0,
            "search_modes": ["broad","exact","negative","primary","freshness","source_specific"] if collection else [],
            "source_families": SOURCE_FAMILIES,
            "required_outputs": ["sources.json","claims.json","evidence.json","errors.json"] if collection else ["result.json"]
        })
    return units

def ensure_interface_context(root, task, run_id, job_id, command_id, request_id, provider, interface, locale):
    interface_path = root / "interface" / "interface-request.json"
    normalized_path = root / "interface" / "normalized-command.json"
    job_path = root / "jobs" / "runtime-job.json"
    outbox_policy_path = root / "outbox" / "outbox-policy.json"

    if interface_path.exists():
        data = jread(interface_path)
        data.update({"run_id": run_id, "job_id": job_id, "command_id": command_id})
        jwrite(interface_path, data)
    else:
        jwrite(interface_path, {
            "request_id": request_id,
            "run_id": run_id,
            "job_id": job_id,
            "command_id": command_id,
            "interface": interface,
            "provider": provider,
            "conversation_id": "direct-runtime",
            "message_id": "0",
            "user_id": "local-user",
            "command": "/research_factory_orchestrator",
            "raw_text": task,
            "attachments": [],
            "adapter_version": VERSION,
            "created_at": now()
        })
    if normalized_path.exists():
        data = jread(normalized_path)
        data.update({"run_id": run_id, "job_id": job_id, "command_id": command_id, "task": task})
        jwrite(normalized_path, data)
    else:
        jwrite(normalized_path, {
            "command_id": command_id,
            "run_id": run_id,
            "job_id": job_id,
            "request_id": request_id,
            "interface": interface,
            "provider": provider,
            "conversation_id": "direct-runtime",
            "message_id": "0",
            "user_id": "local-user",
            "command": "/research_factory_orchestrator",
            "task": task,
            "attachments": [],
            "created_at": now(),
            "locale": locale,
            "delivery_constraints": {"mobile_safe": True, "no_tables": True, "max_message_chars": 3500, "attachments_allowed": True}
        })
    if job_path.exists():
        data = jread(job_path)
        data.update({"run_id": run_id, "job_id": job_id, "command_id": command_id, "task": task, "status": data.get("status", "created")})
        jwrite(job_path, data)
    else:
        jwrite(job_path, {
            "job_id": job_id,
            "run_id": run_id,
            "command_id": command_id,
            "request_id": request_id,
            "runtime_entrypoint": "scripts/run_research_factory.py",
            "task": task,
            "status": "created",
            "created_from_interface": interface,
            "provider": provider,
            "delivery_profile": "mobile_chat" if interface.endswith("chat") else interface,
            "run_dir": str(root),
            "outbox_dir": str(root / "outbox"),
            "created_at": now()
        })
    if not outbox_policy_path.exists():
        jwrite(outbox_policy_path, {
            "run_id": run_id,
            "job_id": job_id,
            "command_id": command_id,
            "provider": provider,
            "delivery_semantics": "at_least_once_with_idempotency_key",
            "only_delivery_worker_can_mark_delivered": True,
            "created_at": now()
        })

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--mode", default="AUTO_COMPILE_AND_EXECUTE")
    ap.add_argument("--run-id")
    ap.add_argument("--job-id")
    ap.add_argument("--command-id")
    ap.add_argument("--request-id")
    ap.add_argument("--provider", default="cli")
    ap.add_argument("--interface", default="direct_runtime")
    ap.add_argument("--locale", default="ru")
    args=ap.parse_args()
    root=Path(args.project_dir); root.mkdir(parents=True, exist_ok=True)

    seed=hashlib.sha1((args.task+now()).encode("utf-8")).hexdigest()[:10]
    run_id=args.run_id or f"RUN-{seed}"
    job_id=args.job_id or f"JOB-{run_id[4:] if run_id.startswith('RUN-') else seed}"
    command_id=args.command_id or f"CMD-{run_id[4:] if run_id.startswith('RUN-') else seed}"
    request_id=args.request_id or f"REQ-{run_id[4:] if run_id.startswith('RUN-') else seed}"
    slug=slugify(args.task)

    for d in ["interface","jobs","ledgers","checkpoints","failure-packets","sources/source-fetches","claims","evidence","graph","raw-evidence/sources","raw-evidence/extracted-nodes","raw-evidence/raw-claims","raw-evidence/rejected","raw-evidence/provenance","work-units","subagents","report","chat","package","logs","outbox","delivery-acks","provider-payloads"]:
        (root/d).mkdir(parents=True, exist_ok=True)

    ensure_interface_context(root, args.task, run_id, job_id, command_id, request_id, args.provider, args.interface, args.locale)

    units=make_work_units()
    assignments=[]
    for i,wu in enumerate(units,1):
        sa=f"SA-{i:03d}"
        a={"assignment_id":f"A-{i:03d}","run_id":run_id,"job_id":job_id,"subagent_id":sa,"work_unit_id":wu["work_unit_id"],"objective":wu["objective"],"context_packet_path":f"subagents/{sa}/context-packet.json","required_outputs":wu["required_outputs"],"status":"planned"}
        assignments.append(a)
        jwrite(root/"subagents"/sa/"assignment.json", a)
        jwrite(root/"subagents"/sa/"context-packet.json", {"run_id":run_id,"job_id":job_id,"command_id":command_id,"task":args.task,"work_unit_id":wu["work_unit_id"],"axis":wu["axis"],"allowed_scope":["target-relevant collection and analysis"],"forbidden_scope":["unsupported conclusions","unbounded recursion","raw sensitive data in chat/provider messages"],"required_outputs":wu["required_outputs"]})
        jwrite(root/"work-units"/wu["work_unit_id"]/"contract.json", wu)
    run={"run_id":run_id,"job_id":job_id,"command_id":command_id,"request_id":request_id,"topic":args.task,"slug":slug,"created_at":now(),"updated_at":now(),"status":"created","skill_version":VERSION,"mode":args.mode,"paths":{"html_report":"report/full-report.html","research_package":"package/research-package.zip","chat_plan":"chat/chat-message-plan.json"}}
    jwrite(root/"run.json", run)
    jwrite(root/"run-state.json", {"run_id":run_id,"job_id":job_id,"status":"created","current_state":"created","completed_states":[],"last_checkpoint_at":now(),"resume_from":None,"errors":[]})
    jwrite(root/"task-profile.json", {"task_id":run_id,"run_id":run_id,"job_id":job_id,"topic":args.task,"detected_entities":[],"claim_types":[],"uncertainty_axes":["entity_ambiguity","source_independence","current_vs_historical","self_claim_vs_external"],"source_family_needs":SOURCE_FAMILIES,"created_at":now()})
    jwrite(root/"coverage-matrix.json", {"task_id":run_id,"run_id":run_id,"axes":[{"axis_id":f"AX-{i:03d}","axis":axis,"required":True,"reason":f"Universal coverage axis {axis}","status":"planned","work_unit_ids":[units[i-1]["work_unit_id"]]} for i,axis in enumerate(AXES,1)],"minimum_axes_required":8,"complete":False})
    jwrite(root/"work-unit-plan.json", {"task_id":run_id,"run_id":run_id,"job_id":job_id,"min_work_units":8,"work_units":units,"compiled_at":now(),"status":"planned"})
    jwrite(root/"subagent-plan.json", {"task_id":run_id,"run_id":run_id,"job_id":job_id,"min_subagents":8,"required_quorum":max(6,len(assignments)-2),"assignments":assignments,"created_at":now()})
    jwrite(root/"subagent-ledger.json", {"task_id":run_id,"run_id":run_id,"job_id":job_id,"required_quorum":max(6,len(assignments)-2),"subagents":[],"subagents_total":0,"subagents_completed":0,"subagents_failed":0,"quorum_met":False})
    jwrite(root/"collection-coverage-contract.json", {"task_id":run_id,"run_id":run_id,"minimum_work_units":8,"minimum_collection_work_units":6,"minimum_search_modes":["broad","exact","negative","primary","freshness","source_specific"],"minimum_source_families":5,"minimum_independent_sources":20,"required_source_families":SOURCE_FAMILIES})
    jwrite(root/"collection-coverage-result.json", {"task_id":run_id,"run_id":run_id,"work_units_completed":0,"collection_work_units_completed":0,"search_modes_present":[],"source_families_present":[],"independent_sources_count":0,"passed":False,"errors":["not executed"]})
    jwrite(root/"ledgers/search-ledger.json", {"task_id":run_id,"run_id":run_id,"searches":[],"total_searches":0,"created_at":now()})
    jwrite(root/"ledgers/tool-call-ledger.json", {"task_id":run_id,"run_id":run_id,"tool_calls":[]})
    jwrite(root/"ledgers/progress-ledger.json", {"task_id":run_id,"run_id":run_id,"events":[]})
    jwrite(root/"ledgers/retry-ledger.json", {"task_id":run_id,"run_id":run_id,"retries":[]})
    jwrite(root/"claims/claims-registry.json", {"run_id":run_id,"claims":[]})
    jwrite(root/"evidence/evidence-cards.json", {"run_id":run_id,"evidence_cards":[]})
    jwrite(root/"graph/target-graph.json", {"run_id":run_id,"target_node_id":"","nodes":[],"edges":[],"created_at":now()})
    jwrite(root/"raw-evidence/raw-evidence-vault.json", {"run_id":run_id,"sources":[],"extracted_nodes":[],"raw_claims":[],"rejected":[],"provenance":[],"created_at":now()})
    jwrite(root/"provenance-manifest.json", {"run_id":run_id,"entities":[],"activities":[],"agents":[],"relations":[],"created_at":now()})
    jwrite(root/"artifact-manifest.json", {"run_id":run_id,"artifacts":[],"updated_at":now()})
    jwrite(root/"validation-transcript.json", {"run_id":run_id,"validators":[],"all_passed":False,"created_at":now()})
    jwrite(root/"delivery-manifest.json", {"run_id":run_id,"job_id":job_id,"command_id":command_id,"delivery_status":"created","attachments":[],"chat_messages":[],"local_paths_exposed":False,"created_at":now()})
    jwrite(root/"attachment-ledger.json", {"run_id":run_id,"job_id":job_id,"command_id":command_id,"attachments":[],"all_required_sent":False})
    jwrite(root/"final-answer-gate.json", {"run_id":run_id,"job_id":job_id,"command_id":command_id,"passed":False,"checks":{},"created_at":now()})
    jwrite(root/"report/semantic-report.json", {"report_meta":run,"summary":{},"sections":[],"claims":[],"sources":[]})
    twrite(root/"report/full-report.html", "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'></head><body><h1>Runtime initialization report shell</h1><script type='application/json' id='artifact-manifest-json'>{}</script><script type='application/json' id='provenance-manifest-json'>{}</script><script type='application/json' id='validation-transcript-json'>{}</script><script type='application/json' id='delivery-manifest-json'>{}</script><script type='application/json' id='runtime-status-json'>{}</script><script type='application/json' id='entrypoint-proof-json'>{}</script></body></html>")
    chat_plan={"run_id":run_id,"job_id":job_id,"command_id":command_id,"provider":args.provider,"plain_text_only":True,"mobile_safe":True,"no_tables":True,"no_local_paths":True,"split_policy":{"max_message_chars":3500,"logical_blocks":True},"messages":[],"attachments":[],"created_at":now()}
    jwrite(root/"chat/chat-message-plan.json", chat_plan)
    event(root, "rfo.runtime.initialized", run_id=run_id, job_id=job_id, command_id=command_id)
    print(root)

if __name__=="__main__":
    main()
