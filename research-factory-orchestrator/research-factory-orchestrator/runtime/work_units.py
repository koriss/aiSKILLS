"""Work-unit executor (RFO v19.2.0).

Closes the v19.0.4 bug class WORK-UNIT-NOT-EXECUTED: cmd_run used to plan WUs
and immediately publish render artifacts, leaving every wu_id stuck at
``planned``. This module iterates over ``work-queue/pending/WU-*.json``,
transitions each WU through the ledger lifecycle, writes per-WU evidence,
emits canonical observability events, and produces a deterministic execution
summary. It is honest about seed-only mode: WUs that did not collect external
sources are reported as ``completed_no_sources`` (NOT silently ``completed``),
which Phase 4B coverage decoupling and Phase 6 production-claim hygiene rely
on.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from runtime.util import jl, jr, jw, now, sha


class WUStatus:
    """Closed enumeration of work-unit lifecycle states (RFO v19.2.0).

    Plain class with frozen ``ALL`` and ``TERMINAL`` sets so external readers
    (validators, replay tools, judges) can typecheck status strings without
    pulling in ``enum`` boilerplate. The constants below are the **only**
    legal values for ``work-unit-ledger.json:work_units[].status``.
    """

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPLETED_NO_SOURCES = "completed_no_sources"
    FAILED = "failed"
    SKIPPED = "skipped"

    TERMINAL = frozenset({COMPLETED, COMPLETED_NO_SOURCES, FAILED, SKIPPED})
    ALL = frozenset({PLANNED, IN_PROGRESS, *TERMINAL})

    @classmethod
    def is_terminal(cls, value: object) -> bool:
        return isinstance(value, str) and value in cls.TERMINAL

    @classmethod
    def is_known(cls, value: object) -> bool:
        return isinstance(value, str) and value in cls.ALL


# Backwards-compatible aliases (old callers).
WU_PENDING = WUStatus.PLANNED
WU_RUNNING = WUStatus.IN_PROGRESS
WU_TERMINAL = tuple(sorted(WUStatus.TERMINAL))


def _emit(rd: Path, name: str, payload: dict) -> None:
    jl(rd / "observability-events.jsonl", {"event_name": name, **payload})
    if os.environ.get("RFO_LEGACY_EVENT_NAMES") == "1":
        jl(rd / "observability-events.jsonl", {"event_name": "v18." + name, **payload, "legacy_alias": True})


def _wu_evidence(rd: Path, wu: dict, sources_collected: int, status: str, started_at: str, completed_at: str) -> Path:
    ev = {
        "schema_version": "v19.0",
        "wu_id": wu["wu_id"],
        "wave": wu.get("wave"),
        "run_id": wu.get("run_id"),
        "job_id": wu.get("job_id"),
        "target_fingerprint": wu.get("target_fingerprint"),
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "sources_collected": int(sources_collected),
        "external_collection_executed": False,
        "evidence_kind": "seed_only_baseline" if status == "completed_no_sources" else status,
        "context_packet_path": wu.get("context_packet"),
    }
    out_dir = rd / "work-queue" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{wu['wu_id']}.evidence.json"
    jw(out_path, ev)
    ev["evidence_sha256"] = sha(out_path)
    jw(out_path, ev)
    return out_path


def execute_pending(rd: Path, run_id: str, job_id: str, *, mode: str, profile: str | None = None) -> dict[str, Any]:
    """Execute every pending WU under <rd>/work-queue/pending/.

    Returns an execution summary suitable for ``work-queue/execution-summary.json``.
    Honest semantics:
      * baseline (no external collector wired) → every WU terminates as
        ``completed_no_sources``;
      * status ``completed`` is reserved for WUs that actually collected
        ≥1 evidence-bearing source (Phase 4 collector, Phase 4B coverage).
    """
    rd = Path(rd)
    pending_dir = rd / "work-queue" / "pending"
    in_progress_dir = rd / "work-queue" / "in_progress"
    done_dir = rd / "work-queue" / "done"
    in_progress_dir.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = rd / "work-queue" / "work-unit-ledger.json"
    ledger = jr(ledger_path, {})
    by_id = {wu["wu_id"]: wu for wu in ledger.get("work_units", [])}
    started_summary: list[dict] = []
    pending_files = sorted(pending_dir.glob("WU-*.json"))
    for pf in pending_files:
        wu = jr(pf, {})
        wu_id = wu.get("wu_id") or pf.stem
        ledger_entry = by_id.get(wu_id, {})
        ledger_entry["status"] = WUStatus.IN_PROGRESS
        ledger_entry["started_at"] = now()
        ledger_entry["mode"] = mode
        if profile:
            ledger_entry["profile"] = profile
        by_id[wu_id] = ledger_entry
        started_at = ledger_entry["started_at"]
        _emit(rd, "work_unit_started", {"run_id": run_id, "job_id": job_id, "wu_id": wu_id, "wave": wu.get("wave"), "timestamp": started_at})
        # Move pending → in_progress
        in_path = in_progress_dir / pf.name
        pf.replace(in_path)
        # Baseline: no collector wired, every WU terminates honestly as completed_no_sources.
        sources_collected = 0
        terminal_status = WUStatus.COMPLETED_NO_SOURCES
        completed_at = now()
        ev_path = _wu_evidence(rd, {**wu, "run_id": run_id, "job_id": job_id}, sources_collected, terminal_status, started_at, completed_at)
        ledger_entry.update(
            {
                "status": terminal_status,
                "completed_at": completed_at,
                "evidence_path": str(ev_path.relative_to(rd)),
                "sources_collected": sources_collected,
                "external_collection_executed": False,
            }
        )
        # in_progress → done
        done_path = done_dir / pf.name
        in_path.replace(done_path)
        _emit(
            rd,
            "work_unit_completed",
            {
                "run_id": run_id,
                "job_id": job_id,
                "wu_id": wu_id,
                "wave": wu.get("wave"),
                "timestamp": completed_at,
                "status": terminal_status,
                "sources_collected": sources_collected,
            },
        )
        started_summary.append({"wu_id": wu_id, "status": terminal_status, "sources_collected": sources_collected})
    ledger["work_units"] = list(by_id.values())
    ledger["last_executor_run_at"] = now()
    jw(ledger_path, ledger)
    summary = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "job_id": job_id,
        "mode": mode,
        "profile": profile,
        "executor_completed_at": now(),
        "total_planned": len(pending_files),
        "total_terminal": len(started_summary),
        "by_status": {},
        "any_collected_sources": any(s["sources_collected"] > 0 for s in started_summary),
        "work_units": started_summary,
    }
    for s in started_summary:
        summary["by_status"][s["status"]] = summary["by_status"].get(s["status"], 0) + 1
    jw(rd / "work-queue" / "execution-summary.json", summary)
    return summary
