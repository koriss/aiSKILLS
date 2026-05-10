"""Runtime worker: execute deterministic render pipeline and package."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from runtime.render import hydrate_claims_if_needed, render_all
from runtime.schema_defaults import minimal_valid
from runtime.status import VERSION
from runtime.util import CHAT, PKG_REQUIRED, REQ_EVENTS, jw, jr, jl, now, sha, sid, skill_root, tw
from runtime.citation_grounding import evaluate as _evaluate_citation_grounding
from runtime.collector import collect as _collect_external
from runtime.coverage import reconcile as _reconcile_coverage
from runtime.profiles import resolve as _resolve_profile
from runtime.work_units import execute_pending as _execute_work_units


def _emit_event(rd: Path, name: str, payload: dict) -> None:
    """Emit canonical v19 event (no legacy aliases)."""
    jl(rd / "observability-events.jsonl", {"event_name": name, **payload})


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
    # v19.2.1 honesty hardening: persist the canonical skill_root, consent
    # flags, and runs_root so the verifier can check whether this run was
    # launched from the right place. ``skill_root()`` already resolves to
    # ``Path(__file__).parent.parent`` for the worker module.
    try:
        sk_root = str(skill_root().resolve())
    except Exception:
        sk_root = ""
    consent = {
        "tmp_runs_root": os.environ.get("RFO_ALLOW_TMP_RUNS_ROOT") == "1",
        "env_chat_id": os.environ.get("RFO_ALLOW_ENV_CHAT_ID") == "1",
    }
    runs_root_str = ""
    try:
        runs_root_str = str(Path(getattr(a, "runs_root", "")).resolve()) if getattr(a, "runs_root", None) else ""
    except Exception:
        runs_root_str = str(getattr(a, "runs_root", "") or "")
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
        "skill_root": sk_root,
        "runs_root": runs_root_str,
        "consent": consent,
        "rfo_allow_tmp_runs_root": consent["tmp_runs_root"],
        "rfo_allow_env_chat_id": consent["env_chat_id"],
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
            "entrypoint_skill_root": sk_root,
            "skill_root": sk_root,
            "runs_root": runs_root_str,
            "consent": consent,
            "rfo_allow_tmp_runs_root": consent["tmp_runs_root"],
            "rfo_allow_env_chat_id": consent["env_chat_id"],
            "not_plain_subagent": True,
            "not_skill_md_imitation": True,
        },
    )
    jw(
        rd / "runtime-status.json",
        minimal_valid(
            "runtime-status",
            overrides={
                "run_id": run_id,
                "job_id": job_id,
                "command_id": cmd_id,
                "state": "content_rendered",
                "version": VERSION,
            },
        ),
    )
    jw(
        rd / "delivery-manifest.json",
        minimal_valid(
            "delivery-manifest",
            overrides={
                "run_id": run_id,
                "job_id": job_id,
                "delivery_status": "not_queued",
                "stub_delivery": False,
                "stub_delivery_disclosure_required": False,
            },
        ),
    )
    jw(rd / "attachment-ledger.json", {"run_id": run_id, "job_id": job_id, "command_id": cmd_id, "attachments": []})
    jw(
        rd / "final-answer-gate.json",
        minimal_valid(
            "final-answer-gate",
            overrides={
                "run_id": run_id,
                "passed": False,
                "status": "content_ready_delivery_not_proven",
            },
        ),
    )
    _emit_event(rd, "runtime.started", {"run_id": run_id, "job_id": job_id, "timestamp": now()})
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
            "provider_outbound_real_send": "stub",
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
    work_units_path = rd / "work-units.json"
    decomposition_path = rd / "decomposition.json"
    wus = []
    if work_units_path.is_file():
        loaded = jr(work_units_path, {})
        candidate = loaded.get("work_units") if isinstance(loaded, dict) else []
        if isinstance(candidate, list):
            wus = [wu for wu in candidate if isinstance(wu, dict) and wu.get("wu_id")]
    elif decomposition_path.is_file():
        loaded = jr(decomposition_path, {})
        candidate = loaded.get("work_units") if isinstance(loaded, dict) else []
        if isinstance(candidate, list):
            wus = [wu for wu in candidate if isinstance(wu, dict) and wu.get("wu_id")]

    for wu in wus:
        wu_id = str(wu.get("wu_id", ""))
        if not wu_id:
            continue
        packet = {**ctx_base, "wu_id": wu_id, "context_packet_hash": sid("CTX", run_id, job_id, wu_id, a.task), "must_return_context_packet_hash_seen": True}
        jw(rd / f"context-packets/{wu_id}.context.json", packet)
        wu.setdefault("status", "planned")
        wu.setdefault("context_packet", f"context-packets/{wu_id}.context.json")

    jw(rd / "work-queue/work-unit-ledger.json", {"run_id": run_id, "job_id": job_id, "work_units": wus, "acceptance_gate": ["run_id", "job_id", "wu_id", "target_fingerprint", "context_packet_hash_seen", "schema_valid"]})
    for wu in wus:
        jw(rd / f"work-queue/pending/{wu['wu_id']}.json", {**wu, "run_id": run_id, "job_id": job_id, "target_fingerprint": ctx_base["target_fingerprint"]})
    tw(rd / "late-results-ledger.jsonl", json.dumps({"event_name": "late_window_opened", "run_id": run_id, "policy": "timeout results require accept/reject + amendment before finality", "timestamp": now()}, ensure_ascii=False) + "\n")
    tw(rd / "amendment-ledger.jsonl", json.dumps({"event_name": "no_amendments_yet", "run_id": run_id, "timestamp": now()}, ensure_ascii=False) + "\n")
    profile_env = os.environ.get("RFO_RUN_PROFILE")
    try:
        profile_name, profile_policy = _resolve_profile(profile_env)
    except ValueError as exc:
        print(json.dumps({"error": "run_profile_resolution", "detail": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from exc
    jw(rd / "run-profile.json", {"schema_version": "v19.0", "profile": profile_name, "policy": profile_policy, "resolved_from": profile_env or "default", "resolved_at": now()})
    wu_summary = _execute_work_units(rd, run_id, job_id, mode=mode, profile=profile_name)
    feature_matrix["features"]["wave_graph_collector"] = (
        "implemented_seed_only" if wu_summary["total_terminal"] == wu_summary["total_planned"] else "scaffold"
    )
    if wu_summary["total_planned"] == 0:
        feature_matrix["features"]["work_unit_decomposition"] = "missing"
    feature_matrix["features"]["work_unit_executor"] = "implemented"
    feature_matrix["work_unit_summary"] = {
        "total_planned": wu_summary["total_planned"],
        "total_terminal": wu_summary["total_terminal"],
        "by_status": wu_summary["by_status"],
        "any_collected_sources": wu_summary["any_collected_sources"],
    }
    collection_summary = _collect_external(rd, run_id=run_id, job_id=job_id, profile=profile_name)
    coverage_result = _reconcile_coverage(rd, run_id=run_id, job_id=job_id, profile=profile_name)
    hydrate_claims_if_needed(rd, a.task, run_id=run_id)
    citation_result = _evaluate_citation_grounding(rd, run_id=run_id, job_id=job_id, profile=profile_name)
    feature_matrix["features"]["external_collector"] = (
        "implemented_real" if collection_summary.get("external_web_search_executed") or collection_summary.get("external_source_packet_loaded") else "implemented_seed_only"
    )
    feature_matrix["collection_summary"] = {
        "backend": collection_summary.get("backend"),
        "external_web_search_executed": collection_summary.get("external_web_search_executed", False),
        "external_source_packet_loaded": collection_summary.get("external_source_packet_loaded", False),
        "web_search_attempted": collection_summary.get("web_search_attempted", False),
        "web_search_succeeded": collection_summary.get("web_search_succeeded", False),
        "web_search_result_count": collection_summary.get("web_search_result_count", 0),
        "external_source_count": collection_summary.get("external_source_count", 0),
        "seed_only": collection_summary.get("seed_only", True),
    }
    feature_matrix["coverage_summary"] = {
        "profile": coverage_result.get("profile"),
        "minimum_independent_sources": coverage_result.get("minimum_independent_sources"),
        "observed_independent_sources": coverage_result.get("observed_independent_sources"),
        "source_coverage_passed": coverage_result.get("source_coverage_passed"),
        "collection_completed": coverage_result.get("collection_completed"),
        "passed": coverage_result.get("passed"),
        "failure_reasons": coverage_result.get("failure_reasons", []),
    }
    feature_matrix["citation_grounding_summary"] = {
        "raf": citation_result.get("relevance_aware_factuality_score"),
        "dfl": citation_result.get("deflection_rate_when_no_grounding"),
        "passed": citation_result.get("passed"),
        "requires_grounding": citation_result.get("requires_grounding"),
        "claims_total": citation_result.get("claims_total"),
        "claims_grounded": citation_result.get("claims_grounded"),
    }
    jw(rd / "feature-truth-matrix.json", feature_matrix)
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
    _emit_event(rd, "runtime.completed", {"run_id": run_id, "job_id": job_id, "timestamp": now()})
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


def _is_seed_only_or_artifact_only(rd: Path) -> bool:
    rd = Path(rd)
    profile_names: set[str] = set()
    for rel in ("run-profile.json", "validation-profile-used.json"):
        p = rd / rel
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            name = str(data.get("profile") or data.get("name") or "").strip().lower()
            if name:
                profile_names.add(name)
    if "artifact-only" in profile_names or "artifact_only" in profile_names:
        return True
    c = jr(rd / "collection-result.json", {})
    if isinstance(c, dict) and c.get("seed_only") is True:
        return True
    rp = jr(rd / "run.json", {})
    if isinstance(rp, dict):
        mode = str(rp.get("mode") or "").strip().lower()
        if mode in {"artifact_only", "artifact-only"}:
            return True
    return False


def _collect_profile_names(rd: Path) -> set[str]:
    names: set[str] = set()
    rd = Path(rd)
    for rel in ("run-profile.json", "validation-profile-used.json"):
        p = rd / rel
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            name = str(data.get("profile") or data.get("name") or "").strip().lower()
            if name:
                names.add(name)
    return names


def _build_package_allow_stub(rd: Path) -> bool:
    """Zip packaging may skip strict PKG_REQUIRED paths for seed/artifact-only/live-bridge prefetch."""
    if _is_seed_only_or_artifact_only(rd):
        return True
    profiles = _collect_profile_names(rd)
    if "live-bridge" in profiles:
        cr = jr(rd / "collection-result.json", {})
        if isinstance(cr, dict) and (
            cr.get("external_source_packet_loaded") or cr.get("external_web_search_executed")
        ):
            return True
    return False


def build_package(rd, *, allow_stub: bool = False, quiet: bool = False):
    rd = Path(rd)
    miss = [r for r in PKG_REQUIRED if not (rd / r).exists()]
    if miss and not allow_stub:
        raise SystemExit("missing required package paths: " + ", ".join(miss))
    pkg = rd / "package/research-package.zip"
    pkg.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pkg, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(rd.rglob("*")):
            if p.is_file() and not p.relative_to(rd).as_posix().startswith("package/") and "__pycache__" not in p.parts and p.suffix != ".pyc":
                z.write(p, p.relative_to(rd).as_posix())
    m = {"package_path": "package/research-package.zip", "size_bytes": pkg.stat().st_size, "sha256": sha(pkg), "built_at": now()}
    jw(rd / "package/research-package-manifest.json", m)
    jw(
        rd / "package/manifest.json",
        {
            "schema_version": "v19.0",
            "mode": "artifact_only" if allow_stub else "full",
            "required_paths_total": len(PKG_REQUIRED),
            "present_paths_count": len(PKG_REQUIRED) - len(miss),
            "missing_paths": miss,
            "missing_policy": "artifact_only_seed_only_skip" if allow_stub else "strict",
            "built_at": now(),
        },
    )
    if not quiet:
        print(json.dumps(m, ensure_ascii=False, indent=2))


def _unlink_stale_lease(lease: Path, ttl_s: float) -> None:
    if not lease.is_file() or ttl_s <= 0:
        return
    try:
        age = time.time() - lease.stat().st_mtime
    except OSError:
        return
    if age >= ttl_s:
        lease.unlink(missing_ok=True)


def _return_job_pending(runq_path: Path, pending_path: Path) -> None:
    if not runq_path.is_file():
        return
    try:
        runq_path.replace(pending_path)
    except OSError:
        pass


def cmd_worker(a):
    root = Path(a.runs_root)
    pending = sorted((root / "queue/pending").glob("*.json"))
    if not pending:
        print(json.dumps({"claimed": False, "reason": "no pending jobs"}))
        return
    if not a.execute_runtime and not a.dry_run:
        raise SystemExit("explicit --execute-runtime or --dry-run required")
    stale_ttl_s = float(os.environ.get("RFO_WORKER_LEASE_STALE_SECONDS", "900"))
    job = jr(pending[0])
    rd = Path(job["run_dir"])
    job_pending_path = pending[0]
    runq = root / "queue/running" / pending[0].name
    done = root / "queue/done" / pending[0].name
    runq.parent.mkdir(parents=True, exist_ok=True)
    done.parent.mkdir(parents=True, exist_ok=True)
    lease = root / "queue/worker.lease"
    tok = sid("LEASE", pending[0].name, now())
    if lease.exists():
        _unlink_stale_lease(lease, stale_ttl_s)
    if lease.exists():
        print(json.dumps({"claimed": False, "reason": "lease_present"}, ensure_ascii=False))
        return
    lease_payload = {
        "token": tok,
        "pid": os.getpid(),
        "job_file": pending[0].name,
        "run_dir": str(rd),
        "created_at": now(),
    }
    lease.write_text(json.dumps(lease_payload, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        job_pending_path.replace(runq)
    except OSError:
        lease.unlink(missing_ok=True)
        raise
    if a.dry_run:
        lease.unlink(missing_ok=True)
        _return_job_pending(runq, job_pending_path)
        raise SystemExit("dry-run intentionally does not execute runtime")
    entry = str(skill_root() / "scripts" / "rfo_runtime_core.py")
    worker_mode = getattr(a, "mode", None) or job.get("run_mode") or "research"
    job_after_move = jr(runq)
    p = None
    try:
        p = subprocess.run(
            [
                sys.executable,
                "-S",
                entry,
                "run",
                "--project-dir",
                str(rd),
                "--task",
                job_after_move["task"],
                "--run-id",
                job_after_move["run_id"],
                "--job-id",
                job_after_move["job_id"],
                "--command-id",
                job_after_move["command_id"],
                "--mode",
                worker_mode,
                "--provider",
                job_after_move.get("provider", "cli"),
                "--interface",
                job_after_move.get("created_from_interface", "generic"),
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        lease.unlink(missing_ok=True)
        _return_job_pending(runq, job_pending_path)
        print(json.dumps({"error": "worker_subprocess_timeout", "timeout_seconds": 240}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(124) from None

    assert p is not None
    if p.returncode:
        lease.unlink(missing_ok=True)
        _return_job_pending(runq, job_pending_path)
        print(p.stdout + p.stderr)
        raise SystemExit(p.returncode)
    jw(
        rd / "outbox/outbox-policy.json",
        {
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "required_events": REQ_EVENTS,
            "policy": "v19 3+1 chat blocks plus html/package files",
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
    build_package(rd, allow_stub=_build_package_allow_stub(rd))
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
