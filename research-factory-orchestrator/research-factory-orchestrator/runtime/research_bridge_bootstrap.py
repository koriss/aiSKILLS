"""Early run_dir layout for Research Factory bridge (relay prefetch).

Creates ``research/``, ``graph/``, incremental logs before relay / adapter.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.util import jl, now


def bootstrap_early_run_dir(rd: Path, *, run_id: str, task: str, label: str = "bridge") -> None:
    """Materialize subtrees and first observability line (partial trace on early failure)."""
    rd = Path(rd)
    for sub in (
        "research",
        "graph",
        "interface",
        "jobs",
        "chat",
        "report",
        "sources",
        "claims",
        "evidence",
        "work-queue",
        "context-packets",
        "package",
    ):
        (rd / sub).mkdir(parents=True, exist_ok=True)
    jl(
        rd / "research" / "bridge-phase-log.jsonl",
        {
            "event_name": "bridge.run_dir_bootstrapped",
            "run_id": run_id,
            "task_preview": (task or "")[:200],
            "label": label,
            "timestamp": now(),
        },
    )
    # Pre-create so host/IDE agents can append steps without inventing a sibling path
    # (see SKILL.md "IDE agent operating sequence").
    trace = rd / "agent-operating-log.md"
    if not trace.exists():
        trace.write_text(
            "# Agent operating trace (RFO)\n\n"
            f"- Canonical run_dir (append steps only here): {rd}\n"
            f"- run_id: {run_id}\n"
            f"- label: {label}\n\n"
            "Append one bullet per step with UTC wall time, command, and exit code. "
            "Do not treat relay stderr snippets or chat/*.md alone as completion proof.\n\n"
            "## Log\n\n",
            encoding="utf-8",
        )


def append_bridge_phase(rd: Path, event_name: str, fields: dict[str, Any] | None = None) -> None:
    row: dict[str, Any] = {"event_name": event_name, "timestamp": now()}
    if fields:
        row.update(fields)
    jl(rd / "research" / "bridge-phase-log.jsonl", row)


def write_off_mode_research_plan(
    rd: Path,
    task: str,
    *,
    queries: list[str],
    safety: dict[str, int],
) -> None:
    """Deterministic plan mirroring template fanout (``RFO_RESEARCH_PLAN_MODE=off``)."""
    doc = {
        "schema_version": "research-plan-v1",
        "metadata": {
            "task": task,
            "plan_version": 1,
            "created_at": now(),
            "mode": "off",
        },
        "axes": [
            {
                "id": "axis-templates",
                "title": "Template relay fanout",
                "intent": "Sequential queries from contracts/query-fanout-config.json",
                "priority": 1,
            }
        ],
        "waves": [
            {
                "wave_id": "W0",
                "axis_id": "axis-templates",
                "purpose": "Deterministic template expansion",
                "queries": list(queries),
            }
        ],
        "safety": safety,
        "extensions": {},
        "evidence_policy": None,
        "stop_when": None,
    }
    p = rd / "research" / "research-plan.json"
    tmp = rd / "research" / ".research-plan.json.tmp"
    research = rd / "research"
    research.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
