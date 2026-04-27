#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_TASK_TYPES = [
        "single_investigation", "batch_investigation", "queue_based_research", "comparative_study",
        "entity_mapping", "source_audit", "fact_checking", "due_diligence", "report_factory",
        "monitoring_setup", "dataset_building", "timeline_reconstruction", "risk_assessment",
        "market_map", "policy_analysis", "technical_research"
]

FSM = [
        "pending", "running_discovery", "running_research", "running_evidence_map", "running_claims_registry",
        "running_draft", "draft_ready", "running_fact_check", "running_citation_locator",
        "running_error_audit", "fixing_output", "validating", "evaluating", "complete"
]

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "runtime-task"

def analyze_request(text: str, queue_mode: str, autonomy_mode: str) -> dict:
    lower = text.lower()
    entities = []
    for m in re.findall(r"`([^`]+)`", text):
        if len(m) < 120:
            entities.append(m)
    task_type = "single_investigation"
    if any(k in lower for k in ["queue", "batch", "factory", "multiple", "per country", "for each"]):
        task_type = "queue_based_research"
    elif "fact-check" in lower or "fact check" in lower:
        task_type = "fact_checking"
    complexity = 1
    if task_type == "queue_based_research":
        complexity = 3
    if any(k in lower for k in ["production", "long-running", "pipeline"]):
        complexity = 4
    queue_required = queue_mode != "none" and (task_type == "queue_based_research" or queue_mode in {"auto", "required"})
    return {
        "main_question": text.strip().splitlines()[0][:240] if text.strip() else "Untitled task",
        "scope": "derived_from_request",
        "domain": "general_research",
        "geography": "unspecified",
        "time_range": "unspecified",
        "entities": entities,
        "expected_outputs": ["final report", "fact-check", "citation locator", "error audit"],
        "source_requirements": ["tiered sources", "traceable citations"],
        "risk_level": "medium",
        "sensitivity_domains": [],
        "queue_required": queue_required,
        "fact_check_required": True,
        "monitoring_required": complexity >= 4,
        "autonomy_mode": autonomy_mode,
        "task_type": task_type,
        "complexity_level": complexity,
    }

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def ensure_scaffold(project_dir: Path, force: bool) -> None:
    script = Path(__file__).with_name("create_project_scaffold.py")
    cmd = ["python3", str(script), "--project-dir", str(project_dir)]
    if force:
        cmd.append("--force")
    subprocess.run(cmd, check=True)

def build_master_prompt(analysis: dict, output_formats: list[str], queue_mode: str, depth_level: str) -> str:
    return f"""# MASTER-PROMPT

Task type: {analysis['task_type']}
Complexity level: {analysis['complexity_level']}
Autonomy mode: {analysis['autonomy_mode']}
Queue mode: {queue_mode}
Depth level: {depth_level}
Output formats: {", ".join(output_formats)}

## Required execution flow
user request
→ compiler
→ generated runtime
→ source collection
→ normalized sources
→ evidence map
→ claims registry
→ draft
→ fact-check
→ citation locator
→ error audit
→ fix output
→ validation
→ final package

## Task launch protocol
- Reload MASTER-PROMPT.md, runtime-contract.json, session-state.md, runtime-state.json, queue.json, artifact-manifest.json at every major stage.
- State files on disk are source of truth.

## Dynamic queue discovery
- Use configured queue source; do not hardcode domain entities.

## Non-stop execution loop
while queue has pending or failed_retryable items:
    reload state
    run stage pipeline
    checkpoint
    continue

## Reliability hardening
Context is disposable. Files are memory. State machine is law. Draft is not final. No source, no claim. No validation, no checkpoint. Pending queue means no stop.

## Finite state machine
{" -> ".join(FSM)}

## Tool registry
- Detect capabilities and write tool-registry.json before first research stage.

## Source policy
- Tier sources and track provenance.

## Evidence and claim model
- Build evidence-map.json and claims-registry.json before finalization.

## Fact-check, citation locator, error audit
- Final output cannot bypass these stages.

## Evaluation rubric
- Enforce thresholds from runtime-contract.json.

## Security model
- Read-only by default. Sensitive actions require explicit approval.

## Definition of Done
- draft exists
- final exists
- fact-check exists
- citation locator with anchors exists
- error audit exists
- validation passes
- evaluation thresholds pass or gaps documented
"""

def main() -> None:
    p = argparse.ArgumentParser(description="Compile user request into research runtime project.")
    p.add_argument("--request-file", required=True)
    p.add_argument("--config", default="")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--output-formats", nargs="+", default=["html"])
    p.add_argument("--queue-mode", default="auto")
    p.add_argument("--depth-level", default="standard", choices=["quick", "standard", "deep", "exhaustive"])
    p.add_argument("--autonomy-mode", default="full_auto", choices=["full_auto", "checkpoint_only", "approve_plan", "approve_sensitive_actions", "manual_review_required"])
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    request_file = Path(args.request_file)
    text = request_file.read_text(encoding="utf-8")
    analysis = analyze_request(text, args.queue_mode, args.autonomy_mode)

    project_dir = Path(args.project_dir)
    ensure_scaffold(project_dir, args.force)

    task_id = slugify(request_file.stem)
    now = iso_now()
    master_prompt = build_master_prompt(analysis, args.output_formats, args.queue_mode, args.depth_level)
    write_text(project_dir / "MASTER-PROMPT.md", master_prompt)

    runtime_contract = {
            "runtime_version": "1.0.0",
            "skill_version": "1.0.0",
            "schema_version": "1.0.0",
            "created_at": now,
            "updated_at": now,
            "migration_required": False,
            "task_id": task_id,
            "task_type": analysis["task_type"] if analysis["task_type"] in ALLOWED_TASK_TYPES else "single_investigation",
            "complexity_level": analysis["complexity_level"],
            "autonomy_mode": args.autonomy_mode,
            "queue_required": analysis["queue_required"],
            "output_formats": args.output_formats,
            "source_policy": {
                "tiers": [1, 2, 3],
                "no_source_no_claim": True,
                "source_limited_mode_enabled": True
            },
            "thresholds": {
                "factual_accuracy": 0.85,
                "citation_accuracy": 0.90,
                "citation_faithfulness": 0.85,
                "source_quality": 0.75,
                "output_contract_compliance": 1.0,
                "safety_compliance": 1.0
            },
            "loop_guards": {
                "MAX_QUEUE_ITERATIONS": 10000,
                "MAX_RESEARCH_LOOPS_PER_ITEM": 5,
                "MAX_FACT_CHECK_PASSES": 2,
                "MAX_CITATION_LOCATOR_PASSES": 2,
                "MAX_ERROR_AUDIT_PASSES": 2,
                "MAX_FIX_PASSES": 2,
                "MAX_RETRIES_PER_STAGE": 2,
                "MAX_TOOL_FAILURES_PER_ITEM": 5,
                "MAX_NO_PROGRESS_STEPS": 3
            },
            "state_machine": {"allowed_sequence": FSM}
    }
    write_json(project_dir / "runtime-contract.json", runtime_contract)

    session_state = f"""# Session State
task_id: {task_id}
status: initialized
current_stage: pending
current_item: {task_id}-item-1
autonomy_mode: {args.autonomy_mode}
queue_required: {analysis['queue_required']}
depth_level: {args.depth_level}
notes: Start from disk state. Do not trust chat memory.
"""
    write_text(project_dir / "session-state.md", session_state)

    runtime_state = {
            "task_id": task_id,
            "current_stage": "pending",
            "current_item_id": f"{task_id}-item-1",
            "status": "pending",
            "allowed_next_stages": FSM[1:],
            "loop_counters": {"queue_iterations": 0, "no_progress_steps": 0},
            "last_progress_at": now,
            "last_artifact_changed": "",
            "blocker": None,
            "next_move": "initialize_tool_registry",
            "updated_at": now
    }
    write_json(project_dir / "runtime-state.json", runtime_state)

    queue_items = [{
            "item_id": f"{task_id}-item-1",
            "item_type": "investigation_target",
            "title": "Primary item from request",
            "slug": "primary-item",
            "priority": "A",
            "reason": "compiled_from_request",
            "status": "pending",
            "output_files": {},
            "evidence_files": {},
            "fact_check_files": {},
            "started_at": None,
            "draft_ready_at": None,
            "completed_at": None,
            "last_error": None,
            "retry_count": 0,
            "max_retries": 2,
            "last_valid_stage": None,
            "blocked_reason": None,
            "force_rebuild": False,
            "is_final_locked": False
    }]
    if analysis["queue_required"]:
        queue_items.append({
                "item_id": f"{task_id}-item-2",
                "item_type": "investigation_target",
                "title": "Secondary item placeholder",
                "slug": "secondary-item",
                "priority": "B",
                "reason": "queue_mode_requires_batch",
                "status": "pending",
                "output_files": {},
                "evidence_files": {},
                "fact_check_files": {},
                "started_at": None,
                "draft_ready_at": None,
                "completed_at": None,
                "last_error": None,
                "retry_count": 0,
                "max_retries": 2,
                "last_valid_stage": None,
                "blocked_reason": None,
                "force_rebuild": False,
                "is_final_locked": False
        })
    write_json(project_dir / "queue.json", {"task_id": task_id, "items": queue_items})

    artifact_manifest = {
            "task_id": task_id,
            "artifacts": [
                {"artifact_id": "master-prompt", "path": "MASTER-PROMPT.md", "role": "manifest", "status": "ready", "checksum": "", "created_at": now, "updated_at": now, "validated_at": now},
                {"artifact_id": "runtime-contract", "path": "runtime-contract.json", "role": "state", "status": "ready", "checksum": "", "created_at": now, "updated_at": now, "validated_at": now},
                {"artifact_id": "queue", "path": "queue.json", "role": "state", "status": "ready", "checksum": "", "created_at": now, "updated_at": now, "validated_at": now}
            ]
    }
    write_json(project_dir / "artifact-manifest.json", artifact_manifest)
    write_json(project_dir / "tool-registry.json", {"tools": []})
    write_json(project_dir / "final-package-manifest.json", {
            "task_id": task_id, "task_title": analysis["main_question"], "project_dir": str(project_dir),
            "completed_items": 0, "skipped_items": 0, "failed_items": 0, "artifacts": [],
            "quality_scores": {}, "known_gaps": ["runtime not executed yet"], "resume_instructions": "Use runtime-state.json and queue.json",
            "rebuild_instructions": "Re-run compile_runtime.py with --force for full rebuild",
            "created_at": now, "updated_at": now
    })
    print(f"Compiled runtime at: {project_dir}")

if __name__ == "__main__":
    main()
