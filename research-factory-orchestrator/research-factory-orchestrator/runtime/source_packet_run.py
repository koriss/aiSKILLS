"""Source-packet-only execute path (no JSON relay prefetch). Used by ``scripts/rfo_execute.py``."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.config_resolution import build_effective_config_snapshot_source_packet_v2, log_startup_summary
from runtime.research_bridge_bootstrap import (
    append_bridge_phase,
    bootstrap_early_run_dir,
    write_off_mode_research_plan,
)
from runtime.research_plan_planner import default_safety_caps
from runtime.render import allocate


def _load_bridge_module(skill_root: Path):
    bridge = skill_root / "scripts" / "run_rfo_with_web_search.py"
    spec = importlib.util.spec_from_file_location("_rfo_relay_bridge_helpers", bridge)
    if spec is None or spec.loader is None:
        raise RuntimeError("bridge module missing")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sources_by_text_kind(sources: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for s in sources:
        if not isinstance(s, dict):
            continue
        vm = str(s.get("verification_mode") or "")
        cs = str(s.get("citation_scope") or "")
        if vm == "snippet_only" or cs == "snippet_only":
            out["snippet"] = out.get("snippet", 0) + 1
        elif vm in ("raw_document", "primary_access") or cs == "raw_document":
            out["full_document"] = out.get("full_document", 0) + 1
        else:
            out["unknown"] = out.get("unknown", 0) + 1
    return out


def _merge_postrun_policy(rd: Path, packet: dict) -> None:
    """Bootstrap PR-1: snippet-heavy web slice → warning + final_verdict_allowed false."""
    from runtime.util import jr, jw

    cr = jr(rd / "collection-result.json", {})
    if not isinstance(cr, dict):
        cr = {}
    sb = _sources_by_text_kind(list(packet.get("sources") or []) if isinstance(packet.get("sources"), list) else [])
    cr["sources_by_text_kind"] = sb
    cr.setdefault("execution_authenticity", packet.get("execution_authenticity"))
    cr.setdefault("evidence_scope", packet.get("evidence_scope"))
    cr.setdefault("collection_integrity", packet.get("collection_integrity"))
    vp = str(packet.get("validation_profile") or "")
    es = str(packet.get("evidence_scope") or "")
    total = sum(sb.values()) or 1
    sn = sb.get("snippet", 0)
    if vp == "bootstrap" and es == "web" and (sn / total) >= 0.5:
        cr["postrun_policy"] = {
            "final_verdict_allowed": False,
            "warnings": ["snippet_heavy_web_bootstrap_threshold"],
        }
    elif str(packet.get("evidence_scope") or "") == "manual":
        cr["postrun_policy"] = {"final_verdict_allowed": False, "warnings": ["manual_evidence_scope_default"]}
    jw(rd / "collection-result.json", cr)


def source_packet_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet_age_hours(created_at: str) -> float:
    raw = (created_at or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return 1e9
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() / 3600.0


def run_source_packet_pipeline(
    *,
    skill_root: Path,
    runs_root: Path,
    task: str,
    packet: dict[str, Any],
    packet_path: Path,
    profile: str,
    argv_for_snapshot: list[str],
) -> int:
    """Allocate run, queue adapter+worker, patch artifacts, emit handoff. Returns process exit code."""
    b = _load_bridge_module(skill_root)
    SCRIPTS_DIR = skill_root / "scripts"
    _ADAPTER_TIMEOUT = float(os.environ.get("RFO_BRIDGE_ADAPTER_TIMEOUT", "120"))
    _WORKER_TIMEOUT = float(os.environ.get("RFO_BRIDGE_WORKER_TIMEOUT", "600"))
    _WORKER_RETRY_MAX = int(os.environ.get("RFO_BRIDGE_WORKER_RETRIES", "12"))
    _WORKER_RETRY_BASE_S = float(os.environ.get("RFO_BRIDGE_WORKER_BACKOFF", "0.35"))

    runs_root_p = runs_root.expanduser().resolve(strict=False)
    b._ensure_rfo_tree(runs_root_p)
    runs_root_s = str(runs_root_p)

    sha = source_packet_sha256(packet_path)
    meta = {
        "validation_profile": packet.get("validation_profile"),
        "execution_authenticity": packet.get("execution_authenticity"),
        "evidence_scope": packet.get("evidence_scope"),
        "collection_integrity": packet.get("collection_integrity"),
    }
    snap = build_effective_config_snapshot_source_packet_v2(
        skill_root=skill_root,
        argv=argv_for_snapshot,
        env=os.environ,
        profile=profile,
        entrypoint="scripts/rfo_execute.py",
        source_packet_path=str(packet_path.resolve()),
        source_packet_sha256=sha,
        packet_meta=meta,
    )
    log_startup_summary(snap)
    errs = snap.get("errors") or []
    if errs or not snap.get("runs_root"):
        print(
            "[fatal] invalid configuration (see stderr [rfo-config-error] lines).",
            file=sys.stderr,
        )
        return 2

    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.path.insert(0, str(skill_root))
    from rfo_query_fanout import build_query_vectors as _bv  # noqa: E402

    entry = allocate(runs_root_s, task, "cli", "cli")
    rd_early = Path(entry["run_dir"]).resolve()
    bootstrap_early_run_dir(
        rd_early,
        run_id=str(entry["run_id"]),
        task=task,
        label="source_packet",
    )
    append_bridge_phase(rd_early, "source_packet.allocated", {"run_dir": str(rd_early)})
    caps = default_safety_caps()
    vectors = _bv(task)
    write_off_mode_research_plan(rd_early, task, queries=vectors, safety=caps)
    try:
        (rd_early / "effective-config.json").write_text(
            json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[warn] could not write effective-config.json: {e}", file=sys.stderr)

    packet_disk = packet_path
    env: dict[str, str] = {str(k): str(v) for k, v in os.environ.items()}
    env["RFO_SOURCE_PACKET"] = str(packet_disk.resolve())
    env["RFO_PREALLOCATED_RUN_DIR"] = str(rd_early)
    b._apply_profile_env(env, profile)

    adapter_script = skill_root / "scripts" / "interface_runtime_adapter.py"
    worker_script = SCRIPTS_DIR / "runtime_job_worker.py"

    adapter_cmd: list[str] = [
        sys.executable,
        "-S",
        str(adapter_script),
        "adapter",
        "--runs-root",
        runs_root_s,
        "--interface",
        "cli",
        "--provider",
        "cli",
        "--task",
        task,
    ]

    ad = subprocess.run(
        adapter_cmd,
        cwd=str(skill_root),
        capture_output=True,
        text=True,
        env=env,
        timeout=_ADAPTER_TIMEOUT,
    )
    if ad.returncode != 0:
        print(f"[adapter] exit {ad.returncode}", file=sys.stderr)
        if ad.stderr:
            print(ad.stderr[:2000], file=sys.stderr)
        return 1

    queued = b._parse_stdout_json_object(ad.stdout or "")
    if not queued.get("queued"):
        print("[adapter] did not queue a job", file=sys.stderr)
        return 1
    latest_run = Path(str(queued.get("run_dir"))).resolve()
    if latest_run != rd_early:
        print(f"[adapter] run_dir mismatch expected={rd_early} got={latest_run}", file=sys.stderr)
        return 1

    worker_claimed = False
    last_worker_out = ""
    for attempt in range(_WORKER_RETRY_MAX):
        proc = subprocess.run(
            [
                sys.executable,
                "-S",
                str(worker_script),
                "--runs-root",
                runs_root_s,
                "--execute-runtime",
            ],
            cwd=str(skill_root),
            capture_output=True,
            text=True,
            env=env,
            timeout=_WORKER_TIMEOUT,
        )
        last_worker_out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        summary = b._parse_stdout_json_object(proc.stdout or "")
        b._append_bridge_worker_poll_event(
            latest_run,
            attempt=attempt + 1,
            proc=proc,
            summary=summary,
            runs_root=runs_root_s,
        )
        claimed_ok = summary.get("claimed") is True and (proc.returncode == 0)
        if claimed_ok:
            worker_claimed = True
            break
        if proc.returncode != 0:
            b._write_bridge_worker_failure_meta(
                runs_root_p,
                attempt=attempt + 1,
                returncode=int(proc.returncode or -1),
                stdout_tail=(proc.stdout or "")[-8000:],
                stderr_tail=(proc.stderr or "")[-8000:],
                parsed_summary=summary,
            )
            return 1
        time.sleep(_WORKER_RETRY_BASE_S + 0.12 * attempt)

    if not worker_claimed:
        print("[worker] not claimed after retries", file=sys.stderr)
        print(last_worker_out[:2500], file=sys.stderr)
        return 1

    all_sources = list(packet.get("sources") or [])
    existing_sources_path = latest_run / "sources.json"
    if existing_sources_path.exists():
        try:
            existing = json.loads(existing_sources_path.read_text())
            existing_srcs = existing.get("sources", [])
            seen = {s.get("source_id") for s in all_sources}
            for es in existing_srcs:
                if es.get("source_id") not in seen:
                    all_sources.append(es)
        except Exception:
            pass

    real_claims, real_ev = b.extract_claims_from_content(all_sources, task)
    if real_claims:
        b.patch_claims_registry(latest_run, real_claims, real_ev)
    b.patch_sources_json(latest_run, all_sources)
    b._persist_bridge_source_packet(latest_run, str(packet_disk.resolve()))
    b._merge_relay_fanout_into_collection(latest_run, {})
    b._merge_research_plan_bridge_meta(
        latest_run,
        plan_mode="off",
        planner_summary={"mode": "source_packet_canonical"},
        run_label=str(entry.get("run_label") or ""),
    )
    _merge_postrun_policy(latest_run, packet)

    from runtime.render import render_all
    from runtime.util import jr

    run_json = jr(latest_run / "run.json", {})
    run_id = str(run_json.get("run_id") or "UNKNOWN")
    job_id_gate = str(run_json.get("job_id") or "UNKNOWN")
    cmd_id_gate = str(run_json.get("command_id") or "UNKNOWN")
    render_all(latest_run, task, run_id, job_id_gate, cmd_id_gate, "cli")

    try:
        from runtime.worker_impl import _build_package_allow_stub, build_package as _bridge_build_package

        _bridge_build_package(
            latest_run,
            allow_stub=_build_package_allow_stub(latest_run),
            quiet=True,
        )
    except Exception as e:
        print(f"[package] rebuild (non-fatal): {e}", file=sys.stderr)

    try:
        from runtime.citation_grounding import evaluate as _evaluate_citation_grounding_bridge
        from runtime.util import jr as _jr_b, jw as _jw_b

        rp_doc = _jr_b(latest_run / "run-profile.json", {})
        pname = str(rp_doc.get("profile") or profile or "dossier")
        cg = _evaluate_citation_grounding_bridge(
            latest_run,
            run_id=run_id,
            job_id=job_id_gate,
            profile=pname,
        )
        fm = _jr_b(latest_run / "feature-truth-matrix.json", {})
        if isinstance(fm, dict):
            fm["citation_grounding_summary"] = {
                "raf": cg.get("relevance_aware_factuality_score"),
                "dfl": cg.get("deflection_rate_when_no_grounding"),
                "passed": cg.get("passed"),
                "requires_grounding": cg.get("requires_grounding"),
                "claims_total": cg.get("claims_total"),
                "claims_grounded": cg.get("claims_grounded"),
            }
            _jw_b(latest_run / "feature-truth-matrix.json", fm)
    except Exception as e:
        print(f"[citation] resync (non-fatal): {e}", file=sys.stderr)

    from runtime.artifact_execute_impl import emit_agent_skill_handoff

    _st, exit_code = emit_agent_skill_handoff(latest_run, task)
    return int(exit_code)
