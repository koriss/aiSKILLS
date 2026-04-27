#!/usr/bin/env python3
"""Create or refresh internal runtime layout for research-factory-orchestrator."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(s: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower()).strip("-")
    return out or "task"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Initialize internal research runtime on disk.")
    p.add_argument("--project-dir", required=True, help="Root directory for runtime files")
    p.add_argument("--task-id", default="", help="Task id (default: derived from --title or timestamp)")
    p.add_argument("--title", default="Research task", help="Short task title")
    p.add_argument(
        "--execution-mode",
        default="AUTO_COMPILE_AND_EXECUTE",
        choices=[
            "AUTO_COMPILE_AND_EXECUTE",
            "LIGHTWEIGHT_RESEARCH",
            "FACT_CHECK_ONLY",
            "REPORT_FACTORY",
            "EXECUTE_EXISTING_RUNTIME",
            "RESUME_RUNTIME",
            "AUDIT_EXISTING_REPORT",
            "COMPILE_ONLY",
        ],
    )
    p.add_argument("--force", action="store_true", help="Overwrite non-final seeds when present")
    args = p.parse_args()

    root = Path(args.project_dir).resolve()
    now = iso_now()
    task_id = args.task_id.strip() or slugify(args.title) + "-" + now[:10]

    item_slug = "primary-item"
    item_id = f"{task_id}-{item_slug}"

    contract = {
        "runtime_version": "1.0.0",
        "skill_version": "1.0.0",
        "schema_version": "1.0.0",
        "task_id": task_id,
        "task_title": args.title,
        "execution_mode": args.execution_mode,
        "global_stage": "runtime_compiled",
        "risk_level": "medium",
        "thresholds": {
            "factual_accuracy": 0.85,
            "citation_accuracy": 0.90,
            "citation_faithfulness": 0.85,
            "source_quality": 0.75,
            "output_contract_compliance": 1.0,
            "safety_compliance": 1.0,
        },
        "loop_guards": {
            "MAX_QUEUE_ITERATIONS": 10000,
            "MAX_RESEARCH_LOOPS_PER_ITEM": 5,
            "MAX_NO_PROGRESS_STEPS": 3,
        },
        "security": {"default_read_only": True, "no_untrusted_code_execution": True},
        "created_at": now,
        "updated_at": now,
    }
    state = {
        "task_id": task_id,
        "current_global_stage": "runtime_compiled",
        "current_item_id": item_id,
        "status": "running",
        "allowed_next_global_stages": [
            "executing_runtime",
            "research_running",
            "evidence_mapping",
            "claims_extracting",
            "draft_ready",
            "fact_check_running",
            "citation_locator_running",
            "error_audit_running",
            "fixing_output",
            "validating",
            "final_ready",
            "delivered",
        ],
        "loop_counters": {"queue_iterations": 0, "no_progress_steps": 0},
        "last_progress_at": now,
        "last_artifact_changed": "",
        "blocker": None,
        "next_move": (
            "stop_after_compile_per_user_request"
            if args.execution_mode == "COMPILE_ONLY"
            else "transition_to_executing_runtime_then_research"
        ),
        "updated_at": now,
    }
    queue = {
        "task_id": task_id,
        "items": [
            {
                "item_id": item_id,
                "title": "Primary item",
                "slug": item_slug,
                "item_type": "default",
                "priority": "A",
                "status": "pending",
                "current_stage": "pending",
                "output_files": {},
                "retry_count": 0,
                "max_retries": 2,
                "last_error": None,
                "force_rebuild": bool(args.force),
                "is_final_locked": False,
            }
        ],
    }
    manifest = {
        "task_id": task_id,
        "artifacts": [
            {
                "artifact_id": "contract",
                "path": "runtime-contract.json",
                "role": "state",
                "status": "ready",
                "created_at": now,
                "updated_at": now,
            },
            {
                "artifact_id": "state",
                "path": "runtime-state.json",
                "role": "state",
                "status": "ready",
                "created_at": now,
                "updated_at": now,
            },
        ],
    }
    tools = {"tools": []}

    write_json(root / "runtime-contract.json", contract)
    write_json(root / "runtime-state.json", state)
    write_json(root / "queue.json", queue)
    write_json(root / "artifact-manifest.json", manifest)
    write_json(root / "tool-registry.json", tools)

    item = root / "items" / item_slug
    write_json(item / "sources.json", {"item_id": item_id, "sources": []})
    write_json(item / "evidence-map.json", {"item_id": item_id, "evidence_notes": []})
    write_json(item / "claims-registry.json", {"item_id": item_id, "claims": []})
    write_text(
        item / "draft.html",
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\" /><title>draft</title></head><body><p>draft</p></body></html>\n",
    )
    write_text(
        item / "final.html",
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\" /><title>final</title></head><body><p>final placeholder</p></body></html>\n",
    )
    write_text(item / "context-snapshot.md", f"# context snapshot\n\nitem: {item_id}\n")
    if not (root / "logs" / "trace.jsonl").exists() or args.force:
        (root / "logs").mkdir(parents=True, exist_ok=True)
        trace_bootstrap = {
            "timestamp": now,
            "stage": "runtime_compiled",
            "action": "init_runtime",
            "item_id": item_id,
            "tool_used": "init_runtime.py",
            "artifact_changed": "runtime-contract.json",
            "progress": True,
            "success": True,
            "error": None,
        }
        (root / "logs" / "trace.jsonl").write_text(
            json.dumps(trace_bootstrap, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if not (root / "logs" / "activity-history.html").exists() or args.force:
        write_text(
            root / "logs" / "activity-history.html",
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\" /></head><body><h1>Activity</h1><p>append entries during execution</p></body></html>\n",
        )
    print(f"Initialized runtime at {root} (task_id={task_id})")


if __name__ == "__main__":
    main()
