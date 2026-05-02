"""Run-dir validation DAG and fail-closed rollback on validation errors."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from runtime.schema_defaults import (
    merge_rollback_delivery_manifest,
    merge_rollback_final_answer_gate,
    minimal_valid,
)
from runtime.util import PKG_REQUIRED, jl, jr, jw, now, read_json_or_none, skill_root

V19_PROFILES = frozenset({"mvr", "full-rigor", "propaganda-io", "book-verification"})


def _ensure_rollback_stub_html(rd: Path) -> None:
    """Create physical stub so V6 DELIV-ATT-MISSING does not fire on rollback attachment."""
    from runtime.schema_defaults import ROLLBACK_STUB_HTML

    rep = rd / "report"
    rep.mkdir(parents=True, exist_ok=True)
    stub = rep / "rollback-stub.html"
    if not stub.is_file():
        stub.write_text(ROLLBACK_STUB_HTML, encoding="utf-8")


def _fail_closed_rollback(rd: Path, errs: list) -> None:
    """Truth-gate: validation_failed must roll back optimistic delivery claims."""
    _ensure_rollback_stub_html(rd)
    dm = read_json_or_none(rd / "delivery-manifest.json")
    if not isinstance(dm, dict):
        dm = minimal_valid("delivery-manifest")
    jw(rd / "delivery-manifest.json", merge_rollback_delivery_manifest(dm))
    fg = read_json_or_none(rd / "final-answer-gate.json")
    if not isinstance(fg, dict):
        fg = minimal_valid("final-answer-gate")
    jw(rd / "final-answer-gate.json", merge_rollback_final_answer_gate(fg))
    st = read_json_or_none(rd / "runtime-status.json")
    if not isinstance(st, dict):
        st = minimal_valid("runtime-status")
    st = dict(st)
    st.update({"state": "validation_failed"})
    jw(rd / "runtime-status.json", st)
    jl(
        rd / "observability-events.jsonl",
        {"event_name": "validation.fail_closed_rollback", "status": "ok", "errors_count": len(errs), "timestamp": now()},
    )


def validate(rd):
    rd = Path(rd)
    prof = os.environ.get("RFO_V19_PROFILE", "").strip().lower()
    if prof in V19_PROFILES:
        root = skill_root()
        runner = root / "scripts" / "run_core_validators.py"
        errs: list = []
        if not runner.is_file():
            errs.append({"missing_runner": str(runner)})
        else:
            p = subprocess.run(
                [sys.executable, "-S", str(runner), "--run-dir", str(rd), "--profile", prof],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=600,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            tr = jr(rd / "validation-transcript.json", {})
            if p.returncode != 0 or not tr.get("overall_pass"):
                errs.append(
                    {
                        "v19_core_validators": "fail",
                        "rc": p.returncode,
                        "stderr_tail": (p.stderr or "")[-1200:],
                    }
                )
        if errs:
            _fail_closed_rollback(rd, errs)
        nval = len((jr(rd / "validation-transcript.json", {}) or {}).get("validators") or [])
        out = {"status": "fail" if errs else "pass", "errors": errs, "validators_total": nval, "run_dir": str(rd), "profile": prof, "validation_mode": "v19_core"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if errs else 0
    required = PKG_REQUIRED
    miss = [r for r in required if not (rd / r).exists()]
    htmltxt = (rd / "report/full-report.html").read_text(encoding="utf-8") if (rd / "report/full-report.html").exists() else ""
    errs = []
    if miss:
        errs.append({"missing": miss})
    if "Placeholder" in htmltxt or "tdtd" in htmltxt:
        errs.append({"bad_html": True})
    if "Deep Investigation Agent" in htmltxt and "Research Factory Orchestrator" in htmltxt:
        errs.append({"report_generator_identity_conflict": "Deep Investigation Agent mixed with RFO claim"})
    if "VALIDATION_GATE: PASSED" in htmltxt and ("FAIL" in htmltxt or "TIMEOUT" in htmltxt or "PARTIAL" in htmltxt):
        errs.append({"gate_consistency": "validation passed text conflicts with failed/partial gates"})
    if "research-package.zip" in (rd / "chat/message-004-files.txt").read_text(encoding="utf-8") and not (rd / "package/research-package.zip").exists():
        errs.append({"package_claim_without_zip": True})
    if not (rd / "feature-truth-matrix.json").exists():
        errs.append({"missing_feature_truth_matrix": True})
    if not (rd / "late-results-ledger.jsonl").exists():
        errs.append({"missing_late_results_ledger": True})
    for ctx in ["context-packets/WU-001.context.json", "context-packets/WU-007.context.json"]:
        if not (rd / ctx).exists():
            errs.append({"missing_context_packet": ctx})
    pkg = rd / "package/research-package.zip"
    if pkg.exists():
        try:
            with zipfile.ZipFile(pkg) as z:
                names = set(z.namelist())
                for needed_out in ["outbox/OUT-0005.json", "outbox/OUT-0006.json"]:
                    if needed_out not in names:
                        errs.append({"package_missing_outbox_event": needed_out})
        except Exception as e:
            errs.append({"bad_package_zip": str(e)})
    plan = jr(rd / "chat/chat-message-plan.json")
    kinds = [m.get("kind") for m in plan.get("messages", [])]
    for k in ["analytical_memo", "factual_dossier", "io_propaganda_check", "files_and_delivery_status"]:
        if k not in kinds:
            errs.append({"missing_chat_kind": k})
    cs = jr(rd / "claims/claims-registry.json").get("claims", [])
    bad = [c.get("claim_id") for c in cs if not c.get("status") or not c.get("evidence_card_ids")]
    if bad:
        errs.append({"bad_claims": bad})
    fg = jr(rd / "final-answer-gate.json")
    gates = fg.get("gates", {})
    needed = [
        "provider_ack_gate",
        "external_delivery_gate",
        "final_user_claim_gate",
        "content_gate",
        "wave_graph_gate",
        "io_analysis_gate",
        "self_audit_gate",
        "package_gate",
        "citation_grounding_gate",
    ]
    missing_g = [g for g in needed if g not in gates]
    if missing_g:
        errs.append({"missing_gates": missing_g})
    root = skill_root()
    reg = jr(root / "contracts" / "validator-registry.json", {})
    vlist = reg.get("validators", [])
    dag_errs = []
    run_dir_first = {
        "validate_handoff_envelope",
        "validate_semantic_intent_alignment",
        "validate_schema_field_coverage",
        "validate_snapshot_immutability",
        "validate_outgoing_message_claims",
        "validate_citation_grounding",
        "validate_idempotent_outbox",
        "validate_cross_model_judge",
        "validate_trace_hash_chain",
        "validate_capability_scope",
        "validate_replay_determinism",
        "validate_state_transitions",
        "validate_skill_markdown_injection",
        "validate_quote_supports_claim",
        "validate_no_delivery_after_validation_fail",
        "validate_no_local_paths_in_chat",
        "validate_logical_consistency",
    }
    if not errs:
        for v in vlist:
            vid = v.get("id", "")
            if vid not in run_dir_first:
                continue
            sp = root / v.get("path", "")
            if not sp.is_file():
                continue
            cmd = [sys.executable, "-S", str(sp), str(rd)]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=str(root), env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            if p.returncode != 0:
                dag_errs.append({"validator": vid, "rc": p.returncode, "stderr": (p.stderr or "")[-1200:]})
        vs = root / "scripts" / "validate_skill.py"
        if vs.is_file():
            p = subprocess.run([sys.executable, "-S", str(vs)], capture_output=True, text=True, timeout=180, cwd=str(root), env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            if p.returncode != 0:
                dag_errs.append({"validator": "validate_skill", "rc": p.returncode, "stderr": (p.stderr or "")[-1200:]})
    errs.extend(dag_errs)
    out = {"status": "fail" if errs else "pass", "errors": errs, "validators_total": len(vlist), "run_dir": str(rd)}
    jw(rd / "validation-transcript.json", out)
    if errs:
        _fail_closed_rollback(rd, errs)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errs else 0
