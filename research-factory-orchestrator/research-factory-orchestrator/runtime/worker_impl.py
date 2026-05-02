"""Runtime worker: execute deterministic render pipeline and package."""
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from runtime.render import render_all
from runtime.status import VERSION
from runtime.util import CHAT, PKG_REQUIRED, REQ_EVENTS, jw, jr, jl, now, sha, sid, skill_root, tw


def _normalize_run_mode(requested: str) -> tuple[str, str | None]:
    """Return (canonical_mode, normalized_from). normalized_from is None iff requested already equals canonical."""
    raw = (requested or "").strip() or "research"
    low = raw.lower()
    aliases = {
        "auto_compile_and_execute": "research",
        "auto": "research",
        "compile_and_execute": "research",
        "dev": "research",
        "development": "research",
        "prod": "production",
    }
    if low in ("research", "production", "smoke"):
        canonical = low
    elif low in aliases:
        canonical = aliases[low]
    else:
        canonical = "research"
    normalized_from = None if low == canonical else raw
    return canonical, normalized_from


def cmd_run(a):
    rd = Path(a.project_dir)
    rd.mkdir(parents=True, exist_ok=True)
    run_id = a.run_id or sid("RUN", str(rd), a.task)
    job_id = a.job_id or sid("JOB", run_id, a.task)
    cmd_id = a.command_id or sid("CMD", run_id, a.task)
    if not (rd / "run-catalog-entry.json").exists():
        jw(
            rd / "run-catalog-entry.json",
            {
                "run_id": run_id,
                "job_id": job_id,
                "command_id": cmd_id,
                "run_label": rd.name,
                "run_dir": str(rd),
                "task": a.task,
                "provider": a.provider,
                "interface": a.interface,
                "created_at": now(),
                "version": VERSION,
            },
        )
    requested_mode = getattr(a, "mode", None) or "research"
    mode, normalized_from = _normalize_run_mode(requested_mode)
    run_payload = {
        "run_id": run_id,
        "job_id": job_id,
        "command_id": cmd_id,
        "run_label": rd.name,
        "task": a.task,
        "mode": mode,
        "requested_mode": requested_mode,
        "version": VERSION,
        "started_at": now(),
        "provider": a.provider,
        "interface": a.interface,
    }
    if normalized_from is not None:
        run_payload["normalized_from"] = normalized_from
    jw(rd / "run.json", run_payload)
    jw(
        rd / "entrypoint-proof.json",
        {
            "run_id": run_id,
            "job_id": job_id,
            "command_id": cmd_id,
            "entrypoint": "scripts/run_research_factory.py",
            "entrypoint_version": VERSION,
            "not_plain_subagent": True,
            "not_skill_md_imitation": True,
        },
    )
    jw(rd / "runtime-status.json", {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "state": "content_rendered", "version": VERSION})
    jw(rd / "delivery-manifest.json", {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "delivery_status": "not_queued", "gates": {}})
    jw(rd / "attachment-ledger.json", {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "attachments": []})
    jw(
        rd / "final-answer-gate.json",
        {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "passed": False, "status": "content_ready_delivery_not_proven", "gates": {}},
    )
    jl(rd / "observability-events.jsonl", {"event_name": "v18.runtime.started", "run_id": run_id, "job_id": job_id, "timestamp": now()})
    feature_matrix = {
        "run_id": run_id,
        "version": VERSION,
        "generated_at": now(),
        "features": {
            "skill_discovery_frontmatter": "implemented",
            "interface_adapter": "implemented",
            "runtime_job_worker": "implemented",
            "outbox_delivery_worker": "implemented",
            "wave_graph_collector": "scaffold",
            "real_external_search_workers": "missing",
            "provider_telegram_real_send": "stub",
            "late_result_protocol": "implemented_scaffold",
            "deterministic_html_renderer": "implemented_scaffold",
            "analytical_memo": "scaffold",
            "factual_dossier": "scaffold",
            "io_propaganda_check": "scaffold",
            "self_audit": "scaffold",
        },
        "rule": "Features marked scaffold/stub/missing may not be advertised as completed production capabilities.",
    }
    jw(rd / "feature-truth-matrix.json", feature_matrix)
    ctx_base = {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "target_fingerprint": sid("TARGET", a.task), "task": a.task, "created_at": now()}
    for wu in ["WU-001", "WU-007"]:
        packet = {**ctx_base, "wu_id": wu, "context_packet_hash": sid("CTX", run_id, job_id, wu, a.task), "must_return_context_packet_hash_seen": True}
        jw(rd / f"context-packets/{wu}.context.json", packet)
    wus = [{"wu_id": f"WU-{i:03d}", "wave": "W1" if i <= 6 else "W2", "status": "planned", "context_packet": "context-packets/WU-001.context.json" if i <= 6 else "context-packets/WU-007.context.json"} for i in range(1, 13)]
    jw(rd / "work-queue/work-unit-ledger.json", {"run_id": run_id, "job_id": job_id, "work_units": wus, "acceptance_gate": ["run_id", "job_id", "wu_id", "target_fingerprint", "context_packet_hash_seen", "schema_valid"]})
    for wu in wus:
        jw(rd / f"work-queue/pending/{wu['wu_id']}.json", {**wu, "run_id": run_id, "job_id": job_id, "target_fingerprint": ctx_base["target_fingerprint"]})
    tw(rd / "late-results-ledger.jsonl", json.dumps({"event_name": "late_window_opened", "run_id": run_id, "policy": "timeout results require accept/reject + amendment before finality", "timestamp": now()}, ensure_ascii=False) + "\n")
    tw(rd / "amendment-ledger.jsonl", json.dumps({"event_name": "no_amendments_yet", "run_id": run_id, "timestamp": now()}, ensure_ascii=False) + "\n")
    render_all(rd, a.task, run_id, job_id, cmd_id, a.provider)
    required = [
        "run.json",
        "entrypoint-proof.json",
        "runtime-status.json",
        "report/full-report.html",
        "report/analytical-memo.json",
        "report/factual-dossier.json",
        "report/io-propaganda-check.json",
        "self-audit/runtime-self-audit.json",
        "graph/wave-plan.json",
        "chat/chat-message-plan.json",
    ]
    jw(rd / "artifact-manifest.json", {"run_id": run_id, "artifacts": [{"path": r, "exists": (rd / r).exists()} for r in required], "generated_at": now()})
    jw(rd / "provenance-manifest.json", {"run_id": run_id, "entrypoint": "scripts/run_research_factory.py", "proof_model": "artifact-backed"})
    jw(rd / "validation-transcript.json", {"run_id": run_id, "status": "pending_dag"})
    jl(rd / "observability-events.jsonl", {"event_name": "v18.runtime.completed", "run_id": run_id, "job_id": job_id, "timestamp": now()})
    from runtime.handoff import emit_handoff
    from runtime.trace import append_trace_line

    append_trace_line(
        rd,
        {
            "ts": now(),
            "run_id": run_id,
            "job_id": job_id,
            "phase": "runtime_completed",
            "validator_id": None,
            "model": None,
            "prompt_hash": None,
            "output_hash": None,
            "decision": "content_rendered",
            "duration_ms": None,
            "evidence_refs": [],
        },
    )
    emit_handoff(rd, "init", "run", {"run_id": run_id, "job_id": job_id, "task": a.task}, required_fields=["run_id", "job_id", "task"])
    emit_handoff(rd, "run", "render", {"run_id": run_id, "artifacts_ready": True}, required_fields=["run_id", "artifacts_ready"])
    emit_handoff(rd, "render", "outbox", {"run_id": run_id, "chat_plan": "chat/chat-message-plan.json"}, required_fields=["run_id", "chat_plan"])
    try:
        from runtime.event_history import append_side_effect

        append_side_effect(rd, "runtime_completed", {"run_id": run_id, "job_id": job_id}, {"state": "content_rendered"})
    except Exception:
        pass
    print(json.dumps({"runtime_initialized": True, "run_id": run_id, "job_id": job_id, "version": VERSION, "state": "content_rendered"}, ensure_ascii=False, indent=2))


def build_package(rd):
    rd = Path(rd)
    miss = [r for r in PKG_REQUIRED if not (rd / r).exists()]
    if miss:
        raise SystemExit("missing required package paths: " + ", ".join(miss))
    pkg = rd / "package/research-package.zip"
    pkg.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(rd.rglob("*")):
            if p.is_file() and not p.relative_to(rd).as_posix().startswith("package/") and "__pycache__" not in p.parts and p.suffix != ".pyc":
                z.write(p, p.relative_to(rd).as_posix())
    m = {"package_path": "package/research-package.zip", "size_bytes": pkg.stat().st_size, "sha256": sha(pkg), "built_at": now()}
    jw(rd / "package/research-package-manifest.json", m)
    print(json.dumps(m, ensure_ascii=False, indent=2))


def cmd_worker(a):
    root = Path(a.runs_root)
    pending = sorted((root / "queue/pending").glob("*.json"))
    if not pending:
        print(json.dumps({"claimed": False, "reason": "no pending jobs"}))
        return
    if not a.execute_runtime and not a.dry_run:
        raise SystemExit("explicit --execute-runtime or --dry-run required")
    job = jr(pending[0])
    rd = Path(job["run_dir"])
    runq = root / "queue/running" / pending[0].name
    done = root / "queue/done" / pending[0].name
    runq.parent.mkdir(parents=True, exist_ok=True)
    done.parent.mkdir(parents=True, exist_ok=True)
    lease = root / "queue/worker.lease"
    tok = sid("LEASE", pending[0].name, now())
    if lease.exists():
        print(json.dumps({"claimed": False, "reason": "lease_present"}, ensure_ascii=False))
        return
    lease.write_text(json.dumps({"token": tok, "job_file": pending[0].name, "run_dir": str(rd), "created_at": now()}, ensure_ascii=False) + "\n", encoding="utf-8")
    pending[0].replace(runq)
    if a.dry_run:
        lease.unlink(missing_ok=True)
        raise SystemExit("dry-run intentionally does not execute runtime")
    entry = str(skill_root() / "scripts" / "rfo_v18_core.py")
    worker_mode = getattr(a, "mode", None) or job.get("run_mode") or "research"
    p = subprocess.run(
        [
            sys.executable,
            "-S",
            entry,
            "run",
            "--project-dir",
            str(rd),
            "--task",
            job["task"],
            "--run-id",
            job["run_id"],
            "--job-id",
            job["job_id"],
            "--command-id",
            job["command_id"],
            "--mode",
            worker_mode,
            "--provider",
            job.get("provider", "cli"),
            "--interface",
            job.get("created_from_interface", "generic"),
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    if p.returncode:
        lease.unlink(missing_ok=True)
        print(p.stdout + p.stderr)
        raise SystemExit(p.returncode)
    jw(
        rd / "outbox/outbox-policy.json",
        {
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "required_events": REQ_EVENTS,
            "policy": "v18 3+1 chat blocks plus html/package files",
            "dedup_window_hours": 72,
            "dlq_after_retries": 8,
            "max_retry_backoff_ms": 60000,
            "retry_jitter_ms": 250,
        },
    )
    for eid, kind, path in CHAT:
        jw(
            rd / "outbox" / f"{eid}.json",
            {
                "event_id": eid,
                "run_id": job["run_id"],
                "job_id": job["job_id"],
                "type": "send_message",
                "provider": job.get("provider", "cli"),
                "payload_path": path,
                "payload_kind": kind,
                "required_for_final_delivery": True,
                "status": "pending",
                "idempotency_key": sid("IDEMP", eid, path, job.get("provider", "cli")),
                "created_at": now(),
            },
        )
    jw(
        rd / "outbox/OUT-0005.json",
        {
            "event_id": "OUT-0005",
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "type": "send_file",
            "provider": job.get("provider", "cli"),
            "payload_path": "report/full-report.html",
            "file_kind": "html_report",
            "required_for_final_delivery": True,
            "status": "pending",
            "idempotency_key": sid("IDEMP", "OUT-0005", "report/full-report.html", job.get("provider", "cli")),
            "created_at": now(),
        },
    )
    jw(
        rd / "outbox/OUT-0006.json",
        {
            "event_id": "OUT-0006",
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "type": "send_file",
            "provider": job.get("provider", "cli"),
            "payload_path": "package/research-package.zip",
            "file_kind": "research_package",
            "required_for_final_delivery": True,
            "status": "pending",
            "idempotency_key": sid("IDEMP", "OUT-0006", "package/research-package.zip", job.get("provider", "cli")),
            "created_at": now(),
        },
    )
    build_package(rd)
    try:
        from runtime.event_history import append_side_effect

        append_side_effect(rd, "package_built", {"run_id": job["run_id"], "job_id": job["job_id"]}, {"ok": True})
    except Exception:
        pass
    st = jr(rd / "runtime-status.json")
    st.update({"state": "delivery_queued"})
    jw(rd / "runtime-status.json", st)
    job.update({"status": "done", "runtime_executed": True, "package_built": True, "outbox_events": 6})
    jw(rd / "jobs/runtime-job.json", job)
    jw(done, job)
    runq.unlink(missing_ok=True)
    lease.unlink(missing_ok=True)
    print(json.dumps({"claimed": True, "status": "done", "run_id": job["run_id"], "outbox_events": 6}, ensure_ascii=False, indent=2))
