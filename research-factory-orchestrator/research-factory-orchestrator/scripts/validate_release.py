#!/usr/bin/env python3
"""Unified release verification: skill validation, schema drift, smokes, failure corpus, B4 self-attestation (v19.0.3+)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# B4 / J5: Reality Checker — default NEEDS_WORK unless every REQUIRED gate passed.
REQUIRED_GATES: frozenset[str] = frozenset(
    {
        "validate_skill",
        "check_schema_drift",
        "_audit_composition_schemas",
        "_smoke_subagent_isolation",
        "_smoke_pristine_run",
        "_smoke_rollback_creates_stubs",
        "smoke_telegram_v18",
        "smoke_telegram_v19",
        "failure_corpus",
        "validate_v19_fixture_suite",
        "validate_v19_release_bad_suite",
        "validate_no_delivery_after_validation_fail",
        "validate_logical_consistency",
        "validate_release_report",
    }
)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _sha256_obj(o: object) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def _run(py: str, cmd: list[str], env: dict[str, str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=env)


def _step_tail(name: str, p: subprocess.CompletedProcess[str], extra: dict[str, object] | None = None) -> dict[str, object]:
    row: dict[str, object] = {
        "name": name,
        "rc": p.returncode,
        "stdout_tail": (p.stdout or "")[-4000:],
        "stderr_tail": (p.stderr or "")[-2000:],
    }
    if extra:
        row.update(extra)
    return row


def _smoke_run_dir(smoke_root: Path) -> str:
    latest_path = smoke_root / "index" / "latest.json"
    if not latest_path.is_file():
        return ""
    try:
        return str(json.loads(latest_path.read_text(encoding="utf-8")).get("run_dir") or "")
    except Exception:
        return ""


def _v19_post_smoke_ok(run_dir: str) -> tuple[bool, str]:
    """J5: after smoke rc==0, either overall_pass or rollback closure."""
    if not run_dir or not Path(run_dir).is_dir():
        return False, "missing run_dir"
    rd = Path(run_dir)
    tp = rd / "validation-transcript.json"
    if not tp.is_file():
        return False, "missing validation-transcript.json"
    try:
        tr = json.loads(tp.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"bad transcript: {e}"
    if tr.get("overall_pass") is True:
        return True, ""
    dm = {}
    dmp = rd / "delivery-manifest.json"
    if dmp.is_file():
        try:
            dm = json.loads(dmp.read_text(encoding="utf-8"))
        except Exception:
            pass
    if dm.get("delivery_status") == "validation_failed" and dm.get("real_external_delivery") is False:
        return True, ""
    return False, "v19 smoke without overall_pass and without rollback closure"


def main() -> int:
    out_path = ROOT / "release-validation-transcript.json"
    steps: list[dict[str, object]] = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable

    p = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_skill.py")], env, 600)
    steps.append(_step_tail("validate_skill", p))

    p2 = _run(py, [py, "-S", str(ROOT / "scripts" / "check_schema_drift.py")], env, 120)
    steps.append(_step_tail("check_schema_drift", p2))

    pa = _run(py, [py, "-S", str(ROOT / "scripts" / "_audit_composition_schemas.py")], env, 120)
    steps.append(_step_tail("_audit_composition_schemas", pa))

    ps = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_subagent_isolation.py")], env, 120)
    steps.append(_step_tail("_smoke_subagent_isolation", ps))

    ppr = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_pristine_run.py")], env, 300)
    steps.append(_step_tail("_smoke_pristine_run", ppr))

    prb_st = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_rollback_creates_stubs.py")], env, 300)
    steps.append(_step_tail("_smoke_rollback_creates_stubs", prb_st))

    core = str(ROOT / "scripts" / "rfo_v18_core.py")
    smoke_root_v18 = Path(tempfile.mkdtemp(prefix="rfo-release-smoke-v18-"))
    p3 = _run(
        py,
        [py, "-S", core, "smoke", "--runs-root", str(smoke_root_v18), "--provider", "telegram", "--interface", "telegram"],
        env,
        600,
    )
    smoke_report_v18 = smoke_root_v18 / "smoke-test-report.json"
    run_dir_v18 = _smoke_run_dir(smoke_root_v18)
    steps.append(
        _step_tail(
            "smoke_telegram_v18",
            p3,
            {
                "smoke_report_sha256": _sha256_file(smoke_report_v18) if smoke_report_v18.is_file() else "",
                "smoke_run_dir": run_dir_v18,
            },
        )
    )

    smoke_root_v19 = Path(tempfile.mkdtemp(prefix="rfo-release-smoke-v19-"))
    env_v19 = {**env, "RFO_V19_PROFILE": "mvr"}
    p3b = _run(
        py,
        [py, "-S", core, "smoke", "--runs-root", str(smoke_root_v19), "--provider", "telegram", "--interface", "telegram"],
        env_v19,
        600,
    )
    smoke_report_v19 = smoke_root_v19 / "smoke-test-report.json"
    run_dir_v19 = _smoke_run_dir(smoke_root_v19)
    extra: dict[str, object] = {
        "smoke_report_sha256": _sha256_file(smoke_report_v19) if smoke_report_v19.is_file() else "",
        "smoke_run_dir": run_dir_v19,
    }
    eff_rc = p3b.returncode
    if p3b.returncode == 0 and run_dir_v19:
        ok, note = _v19_post_smoke_ok(run_dir_v19)
        if not ok:
            eff_rc = 1
            extra["v19_closure_error"] = note
    extra["rc_effective"] = eff_rc
    row_v19 = _step_tail("smoke_telegram_v19", p3b, extra)
    row_v19["rc"] = eff_rc
    steps.append(row_v19)

    p4 = _run(py, [py, "-S", core, "failure"], env, 600)
    steps.append(_step_tail("failure_corpus", p4))

    pv19 = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_fixture_suite.py"), "--verbose"], env, 600)
    steps.append(_step_tail("validate_v19_fixture_suite", pv19))

    prb = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_release_bad_suite.py")], env, 120)
    steps.append(_step_tail("validate_v19_release_bad_suite", prb))

    run_dir_nd = run_dir_v18 or run_dir_v19
    nd_rc = 1
    if run_dir_nd and Path(run_dir_nd).is_dir():
        p5 = _run(
            py,
            [py, "-S", str(ROOT / "scripts" / "validate_no_delivery_after_validation_fail.py"), run_dir_nd],
            env,
            120,
        )
        nd_rc = p5.returncode
        steps.append(_step_tail("validate_no_delivery_after_validation_fail", p5, {"run_dir": run_dir_nd}))
    else:
        steps.append({"name": "validate_no_delivery_after_validation_fail", "rc": 1, "error": "no smoke run_dir"})

    skill_ver = ""
    try:
        vf = ROOT / "runtime" / "version.json"
        skill_ver = str(json.loads(vf.read_text(encoding="utf-8")).get("skill_version", ""))
    except Exception:
        pass

    transcript: dict[str, object] = {
        "version": skill_ver or "19.0.3",
        "skill_version": skill_ver,
        "steps": steps,
        "transcript_sha256": "",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lc_rc = 1
    if run_dir_nd and Path(run_dir_nd).is_dir():
        p_lc = _run(
            py,
            [
                py,
                "-S",
                str(ROOT / "scripts" / "validate_logical_consistency.py"),
                run_dir_nd,
                "--transcript",
                str(out_path),
            ],
            env,
            120,
        )
        lc_rc = p_lc.returncode
        steps.append(_step_tail("validate_logical_consistency", p_lc, {"run_dir": run_dir_nd}))
    else:
        steps.append({"name": "validate_logical_consistency", "rc": 1, "error": "no smoke run_dir"})

    transcript["steps"] = steps
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # D1 skeleton (optional, never blocks release)
    if run_dir_v18 and Path(run_dir_v18).is_dir():
        pd = _run(py, [py, "-S", str(ROOT / "scripts" / "_diff_telegram_against_golden.py"), run_dir_v18], env, 60)
        steps.append(_step_tail("_diff_telegram_against_golden", pd, {"run_dir": run_dir_v18}))

    transcript["steps"] = steps
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_arg = os.environ.get("RFO_RELEASE_REPORT_PATH", "").strip()
    cmd = [py, "-S", str(ROOT / "scripts" / "validate_release_report.py"), "--transcript", str(out_path)]
    if report_arg and Path(report_arg).is_file():
        cmd.append(report_arg)
    pr = _run(py, cmd, env, 120)
    steps.append(_step_tail("validate_release_report", pr))

    transcript["steps"] = steps

    passed_names = {str(s.get("name")) for s in steps if s.get("rc") == 0}
    passed_gates = passed_names & REQUIRED_GATES
    missing = sorted(REQUIRED_GATES - passed_gates)
    blocking = list(missing)
    if blocking:
        verdict = "NEEDS_WORK"
        next_actions = [f"resolve gate: {g}" for g in blocking]
    else:
        verdict = "READY"
        next_actions = []
    transcript["overall_verdict"] = verdict
    transcript["human_summary"] = (
        f"REQUIRED_GATES {len(passed_gates)}/{len(REQUIRED_GATES)} passed; "
        f"steps {len(passed_names)}/{len(steps)} rc=0"
    )
    transcript["blocking_failures"] = blocking
    transcript["next_actions"] = next_actions

    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # B4: fail if verdict not READY (includes missing gates)
    failed = verdict != "READY"

    # cleanup temp smoke dirs (best effort)
    for d in (smoke_root_v18, smoke_root_v19):
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass

    print(
        json.dumps(
            {"status": "fail" if failed else "pass", "overall_verdict": verdict, "release_validation_transcript": str(out_path)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
