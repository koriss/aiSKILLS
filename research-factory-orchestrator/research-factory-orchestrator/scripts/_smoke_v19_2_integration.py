#!/usr/bin/env python3
"""RFO v19.2.0 integration smoke matrix.

Closes Phase 5 of the Runtime Truth Restoration plan. Runs an end-to-end
matrix of pristine runs against the v19.2.0 truth gates and asserts:

  * MVR baseline run passes V1 + every truth gate without rollback.
  * full-rigor without backend FAILS the coverage gate (COVERAGE-GATE-FAILED)
    and citation-grounding gate.
  * RFO_EXTERNAL_COLLECTION=required + RFO_NO_NETWORK=1 surfaces
    RFO_EXTERNAL_COLLECTION_REQUIRED_BUT_NO_BACKEND in errors.jsonl.
  * Profile/registry/runner alignment guards PASS.
  * No v18.* event names leak under default RFO_LEGACY_EVENT_NAMES=0.
  * No forbidden legacy mode tokens in production artifacts (code hygiene).
  * subprocess-timeouts validator PASSes for runtime/+scripts/.

stdlib-only, fail-closed; emits a compact JSON ledger on stdout.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 180) -> tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, **(env or {}), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT)},
    )
    return p.returncode, p.stdout or "", p.stderr or ""


def _cli_run(project_dir: Path, *, mode: str = "research", profile: str | None = None, env_extra: dict[str, str] | None = None) -> tuple[int, str, str]:
    env = {"PYTHONPATH": str(ROOT)}
    if profile:
        env["RFO_RUN_PROFILE"] = profile
    if env_extra:
        env.update(env_extra)
    return _run(
        [sys.executable, "-S", "-m", "runtime.cli", "run", "--project-dir", str(project_dir), "--task", "v19.2 integration smoke", "--mode", mode],
        env=env,
        timeout=120,
    )


def _validator(name: str, *, run_dir: Path | None = None) -> tuple[int, dict]:
    args = [sys.executable, "-S", str(ROOT / "scripts" / f"{name}.py")]
    if run_dir is not None:
        args.extend(["--run-dir", str(run_dir)])
    rc, out, _ = _run(args)
    try:
        payload = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except Exception:
        payload = {"_raw": out[-400:]}
    return rc, payload


def _core_validator(rel: str, run_dir: Path) -> tuple[int, dict]:
    args = [sys.executable, "-S", str(ROOT / rel), "--run-dir", str(run_dir)]
    rc, out, _ = _run(args)
    try:
        payload = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except Exception:
        payload = {"_raw": out[-400:]}
    return rc, payload


def _scenario_mvr_baseline(work_root: Path) -> dict:
    rd = work_root / "mvr-baseline"
    rd.mkdir(parents=True, exist_ok=True)
    rc_run, out_run, err_run = _cli_run(rd, profile="mvr")
    if rc_run != 0:
        return {"name": "mvr_baseline", "status": "fail", "stage": "cli_run", "rc": rc_run, "stderr": err_run[-400:]}
    checks: dict[str, bool] = {}
    for v in (
        "validate_work_unit_completion",
        "validate_seed_only_truth",
        "validate_error_log_quality",
        "validate_source_provenance_distinction",
        "validate_collection_coverage_decoupled",
        "validate_v18_legacy_compat",
    ):
        rc, payload = _validator(v, run_dir=rd)
        checks[v] = bool(payload.get("passed"))
    rc_v1, payload_v1 = _core_validator("validators/core/validate_artifact_schema.py", rd)
    checks["validate_artifact_schema"] = bool(payload_v1.get("passed"))
    return {
        "name": "mvr_baseline",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }


def _scenario_full_rigor_without_backend(work_root: Path) -> dict:
    rd = work_root / "full-rigor-no-backend"
    rd.mkdir(parents=True, exist_ok=True)
    rc_run, _, err_run = _cli_run(rd, profile="full-rigor", env_extra={"RFO_NO_NETWORK": "1", "RFO_RUN_PROFILE": "full-rigor"})
    if rc_run != 0:
        return {"name": "full_rigor_no_backend", "status": "fail", "stage": "cli_run", "rc": rc_run, "stderr": err_run[-400:]}
    rc_cov, payload_cov = _validator("validate_collection_coverage_decoupled", run_dir=rd)
    rc_cit, payload_cit = _validator("validate_citation_grounding", run_dir=rd)
    fail_cov = not payload_cov.get("passed")
    fail_cit = not payload_cit.get("passed")
    return {
        "name": "full_rigor_no_backend",
        "status": "pass" if (fail_cov and fail_cit) else "fail",
        "expected": "coverage_fail+citation_fail",
        "coverage_failed": fail_cov,
        "citation_failed": fail_cit,
    }


def _scenario_required_no_network(work_root: Path) -> dict:
    rd = work_root / "required-no-network"
    rd.mkdir(parents=True, exist_ok=True)
    _cli_run(rd, profile="mvr", env_extra={"RFO_NO_NETWORK": "1", "RFO_EXTERNAL_COLLECTION": "required"})
    err_path = rd / "runtime" / "errors.jsonl"
    if not err_path.is_file():
        return {"name": "required_no_network", "status": "fail", "detail": "runtime/errors.jsonl absent"}
    codes = set()
    for line in err_path.read_text(encoding="utf-8").splitlines():
        try:
            codes.add(json.loads(line).get("code"))
        except Exception:
            continue
    has_required = "RFO_EXTERNAL_COLLECTION_REQUIRED_BUT_NO_BACKEND" in codes
    return {
        "name": "required_no_network",
        "status": "pass" if has_required else "fail",
        "codes_seen": sorted(c for c in codes if c),
    }


def _scenario_profile_alignment() -> dict:
    rc, payload = _validator("validate_profile_validator_alignment")
    return {"name": "profile_validator_alignment", "status": "pass" if payload.get("passed") else "fail", "detail": payload}


def _scenario_subprocess_timeouts() -> dict:
    rc, payload = _validator("validate_subprocess_timeouts")
    return {"name": "subprocess_timeouts", "status": "pass" if payload.get("passed") else "fail", "issues": len(payload.get("issues") or [])}


def _scenario_no_v18_event_leak(work_root: Path) -> dict:
    rd = work_root / "v18-event-leak"
    rd.mkdir(parents=True, exist_ok=True)
    _cli_run(rd, profile="mvr")
    events = rd / "observability-events.jsonl"
    if not events.is_file():
        return {"name": "no_v18_event_leak", "status": "fail", "detail": "observability-events.jsonl absent"}
    leaked: list[str] = []
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        name = ev.get("event_name") or ""
        if name.startswith("v18."):
            leaked.append(name)
    return {"name": "no_v18_event_leak", "status": "pass" if not leaked else "fail", "leaked_event_names": leaked[:10]}


def _scenario_no_lightweight_token() -> dict:
    rc, _, err = _run([sys.executable, "-S", str(ROOT / "scripts" / "validate_code_hygiene.py")])
    return {"name": "no_lightweight_token", "status": "pass" if rc == 0 else "fail", "stderr_tail": err[-400:] if rc else ""}


def _scenario_root_vs_zip(work_root: Path) -> dict:
    rd = work_root / "root-vs-zip"
    rd.mkdir(parents=True, exist_ok=True)
    _cli_run(rd, profile="mvr")
    rc, payload = _validator("validate_root_vs_zip_artifact_truth", run_dir=rd)
    # In MVR pristine baseline package isn't always built; allow advisory pass when zip is absent.
    return {"name": "root_vs_zip_artifact_truth", "status": "pass" if payload.get("passed") else "fail", "detail": payload.get("summary", "")}


def _scenario_mvr_no_network_v19_validate(work_root: Path) -> dict:
    """T5.7a: mvr + no network + V1 (run_core) must PASS; coverage gate reflects no external sources."""
    rd = work_root / "mvr-no-net-v19"
    rd.mkdir(parents=True, exist_ok=True)
    env_extra = {"RFO_V19_PROFILE": "mvr", "RFO_NO_NETWORK": "1"}
    rc_run, _, err = _cli_run(rd, profile="mvr", env_extra=env_extra)
    if rc_run != 0:
        return {"name": "mvr_no_network_v19_validate", "status": "fail", "stage": "cli_run", "stderr": err[-400:]}
    rc_val, out, _ = _run(
        [sys.executable, "-S", "-m", "runtime.cli", "validate", "--run-dir", str(rd)],
        env={"PYTHONPATH": str(ROOT), **env_extra},
        timeout=180,
    )
    tr = {}
    tp = rd / "validation-transcript.json"
    if tp.is_file():
        try:
            tr = json.loads(tp.read_text(encoding="utf-8"))
        except Exception:
            tr = {}
    cr = {}
    crp = rd / "collection-result.json"
    if crp.is_file():
        try:
            cr = json.loads(crp.read_text(encoding="utf-8"))
        except Exception:
            cr = {}
    overall = tr.get("overall_pass") is True and rc_val == 0
    backend = str(cr.get("backend") or "")
    net_ok = backend == "no_network"
    return {
        "name": "mvr_no_network_v19_validate",
        "status": "pass" if overall and net_ok else "fail",
        "overall_pass": tr.get("overall_pass"),
        "validate_rc": rc_val,
        "collection_backend": backend,
        "stdout_tail": out[-300:],
    }


def _scenario_source_packet_load(work_root: Path) -> dict:
    """T5.7d: source-packet profile loads operator packet; web search not executed."""
    rd = work_root / "source-packet-prof"
    rd.mkdir(parents=True, exist_ok=True)
    pkt = str(ROOT / "fixtures" / "source-packet-min.json")
    env_extra = {"RFO_V19_PROFILE": "mvr", "RFO_SOURCE_PACKET": pkt}
    rc_run, _, err = _cli_run(rd, profile="source-packet", env_extra=env_extra)
    if rc_run != 0:
        return {"name": "source_packet_load", "status": "fail", "stage": "cli_run", "stderr": err[-400:]}
    ftm = {}
    fp = rd / "feature-truth-matrix.json"
    if fp.is_file():
        try:
            ftm = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            ftm = {}
    cs = ftm.get("collection_summary") or {}
    ok = cs.get("external_source_packet_loaded") is True and cs.get("external_web_search_executed") is False
    return {"name": "source_packet_load", "status": "pass" if ok else "fail", "collection_summary": cs}


def _scenario_legacy_validate_pre_outbox(work_root: Path) -> dict:
    """T5.8: validate without V19 profile must fail-closed (outbox finalization + truth gates)."""
    rd = work_root / "legacy-pre-outbox"
    rd.mkdir(parents=True, exist_ok=True)
    rc_run, _, _ = _cli_run(rd, profile="mvr", env_extra={"RFO_LEGACY_EVENT_NAMES": "0"})
    if rc_run != 0:
        return {"name": "legacy_pre_outbox", "status": "fail", "stage": "cli_run", "rc": rc_run}
    rc_val, _, _ = _run(
        [sys.executable, "-S", "-m", "runtime.cli", "validate", "--run-dir", str(rd)],
        env={"PYTHONPATH": str(ROOT)},
        timeout=180,
    )
    return {"name": "legacy_pre_outbox_validate_fail", "status": "pass" if rc_val != 0 else "fail", "validate_rc": rc_val}


def _scenario_mvr_pristine_v1_pass(work_root: Path) -> dict:
    """T5.1: cmd_run + V1 under RFO_V19_PROFILE without rollback closure."""
    rd = work_root / "mvr-pristine-v1"
    rd.mkdir(parents=True, exist_ok=True)
    env_extra = {"RFO_V19_PROFILE": "mvr"}
    rc_run, _, err = _cli_run(rd, profile="mvr", env_extra=env_extra)
    if rc_run != 0:
        return {"name": "mvr_pristine_v1", "status": "fail", "stage": "cli_run", "stderr": err[-400:]}
    rc_val, _, _ = _run(
        [sys.executable, "-S", "-m", "runtime.cli", "validate", "--run-dir", str(rd)],
        env={"PYTHONPATH": str(ROOT), **env_extra},
        timeout=180,
    )
    tr = {}
    if (rd / "validation-transcript.json").is_file():
        try:
            tr = json.loads((rd / "validation-transcript.json").read_text(encoding="utf-8"))
        except Exception:
            tr = {}
    rollback = False
    obs = rd / "observability-events.jsonl"
    if obs.is_file():
        for line in obs.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("event_name") == "validation.fail_closed_rollback":
                rollback = True
                break
    ok = rc_val == 0 and tr.get("overall_pass") is True and not rollback
    return {"name": "mvr_pristine_v1", "status": "pass" if ok else "fail", "rollback_observed": rollback, "overall_pass": tr.get("overall_pass")}


def _scenario_no_active_legacy_gates_ast() -> dict:
    """T5.11f: forbid ``.get(\"gates\")`` outside legacy_compat."""
    bad: list[str] = []
    roots = [ROOT / "runtime", ROOT / "scripts", ROOT / "validators"]
    pat = re.compile(r'\.get\(\s*["\']gates["\']\s*\)')
    for base in roots:
        if not base.is_dir():
            continue
        for py in base.rglob("*.py"):
            if "legacy_compat.py" in str(py):
                continue
            try:
                text = py.read_text(encoding="utf-8")
            except OSError:
                continue
            if pat.search(text):
                bad.append(str(py.relative_to(ROOT)))
    return {"name": "no_active_legacy_gates_ast", "status": "pass" if not bad else "fail", "hits": bad[:20]}


def _scenario_contract_and_profile_guards() -> dict:
    rc1, p1 = _validator("validate_active_contract_versions")
    rc2, p2 = _validator("validate_profile_policies_present")
    ok = rc1 == 0 and p1.get("passed") and rc2 == 0 and p2.get("passed")
    return {"name": "contract_and_profile_guards", "status": "pass" if ok else "fail", "active_contracts": p1, "profile_policies": p2}


def _scenario_no_v18_emit_strings(work_root: Path) -> dict:
    """T5.4: scan key JSON artifacts for forbidden v18 root emit markers."""
    rd = work_root / "v18-emit-scan"
    rd.mkdir(parents=True, exist_ok=True)
    _cli_run(rd, profile="mvr", env_extra={"RFO_V19_PROFILE": "mvr"})
    needles = ('"taxonomy_version": "v18"', "v18_seed_runtime", "v18.runtime.", "RFO v18")
    hits: list[str] = []
    for rel in ("run.json", "final-answer-gate.json", "runtime-status.json", "delivery-manifest.json"):
        p = rd / rel
        if not p.is_file():
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for n in needles:
            if n in txt:
                hits.append(f"{rel}:{n}")
    return {"name": "no_v18_emit_strings", "status": "pass" if not hits else "fail", "hits": hits}


def _scenario_work_unit_events(work_root: Path) -> dict:
    """T5.2: WU ledger terminal + started/completed event pairs."""
    rd = work_root / "wu-events"
    rd.mkdir(parents=True, exist_ok=True)
    rc_run, _, err = _cli_run(rd, profile="mvr", env_extra={"RFO_V19_PROFILE": "mvr"})
    if rc_run != 0:
        return {"name": "work_unit_events", "status": "fail", "stage": "cli_run", "stderr": err[-400:]}
    rc_wu, payload = _validator("validate_work_unit_completion", run_dir=rd)
    return {"name": "work_unit_events", "status": "pass" if rc_wu == 0 and payload.get("passed") else "fail", "detail": payload}


def main() -> int:
    work_root = Path(tempfile.mkdtemp(prefix="rfo-v192-integration-"))
    try:
        results = [
            _scenario_mvr_baseline(work_root),
            _scenario_full_rigor_without_backend(work_root),
            _scenario_required_no_network(work_root),
            _scenario_profile_alignment(),
            _scenario_subprocess_timeouts(),
            _scenario_no_v18_event_leak(work_root),
            _scenario_no_lightweight_token(),
            _scenario_root_vs_zip(work_root),
            _scenario_mvr_no_network_v19_validate(work_root),
            _scenario_source_packet_load(work_root),
            _scenario_legacy_validate_pre_outbox(work_root),
            _scenario_mvr_pristine_v1_pass(work_root),
            _scenario_no_active_legacy_gates_ast(),
            _scenario_contract_and_profile_guards(),
            _scenario_no_v18_emit_strings(work_root),
            _scenario_work_unit_events(work_root),
        ]
    finally:
        shutil.rmtree(work_root, ignore_errors=True)
    overall = all(r["status"] == "pass" for r in results)
    print(
        json.dumps(
            {
                "smoke_id": "_smoke_v19_2_integration",
                "schema_version": "v19.0",
                "passed": overall,
                "scenarios": results,
            },
            ensure_ascii=False,
        )
    )
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
