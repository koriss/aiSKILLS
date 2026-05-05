#!/usr/bin/env python3
"""Unified release verification: skill validation, schema drift, smokes, failure corpus, B4 self-attestation (v19.0.4+)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
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
        "_smoke_corrupt_render",
        "smoke_telegram_v18",
        "smoke_telegram_v19",
        "smoke_cli_v19",
        "failure_corpus",
        "validate_v19_fixture_suite",
        "validate_v19_release_bad_suite",
        "validate_no_delivery_after_validation_fail",
        "validate_logical_consistency",
        "validate_release_report",
        "_smoke_deterministic_replay",
        "_smoke_trajectory_v19",
        "coverage_meta",
        "release_zip_triad",
        "_smoke_clean_install",
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


class _SP:
    """Synthetic subprocess result for inline release steps."""

    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, rc: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = rc
        self.stdout = stdout
        self.stderr = stderr


_ZIP_SKIP_DIR_PARTS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "release-artifacts",
    }
)


def _build_release_zip_triad(root: Path) -> tuple[int, dict[str, object]]:
    """Stdlib zip + sha256 sidecar + release-manifest.json under ``release-artifacts/``."""
    extra: dict[str, object] = {}
    try:
        ver = str(json.loads((root / "runtime" / "version.json").read_text(encoding="utf-8")).get("skill_version", ""))
    except Exception:
        ver = "19.1.0"
    art = root / "release-artifacts"
    art.mkdir(parents=True, exist_ok=True)
    zip_name = f"research-factory-orchestrator-{ver}.zip"
    zip_path = art / zip_name
    try:
        if zip_path.is_file():
            zip_path.unlink()
    except OSError:
        pass
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    rel = path.relative_to(root)
                except ValueError:
                    continue
                if any(p in _ZIP_SKIP_DIR_PARTS for p in rel.parts):
                    continue
                zf.write(path, arcname=str(rel).replace("\\", "/"))
    except OSError as e:
        extra["error"] = str(e)
        return 1, extra
    data = zip_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    (zip_path.parent / f"{zip_path.name}.sha256").write_text(f"{sha}  {zip_path.name}\n", encoding="utf-8")
    git_commit = ""
    try:
        gr = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=8,
            env=os.environ,
        )
        if gr.returncode == 0:
            git_commit = (gr.stdout or "").strip()
    except Exception:
        git_commit = ""
    manifest: dict[str, object] = {
        "schema_version": "v19.1",
        "release_id": zip_name.replace(".zip", ""),
        "skill_version": ver,
        "git_commit": git_commit,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "builder": "validate_release",
        "zip_name": zip_name,
        "zip_sha256": sha,
        "zip_bytes": len(data),
        "excluded_patterns": sorted(_ZIP_SKIP_DIR_PARTS),
        "zip_path": str(zip_path.relative_to(root)),
    }
    man_path = art / "release-manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    extra.update({"zip_path": str(zip_path), "manifest_path": str(man_path), "zip_sha256": sha})
    return 0, extra


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
    # Release smokes must produce distinct run_id values in the transcript (validate_release_report F199).
    # Host-wide B1 knobs would otherwise collapse IDs across temp smoke roots; dedicated scripts set their own env.
    for _drop in ("RFO_DETERMINISTIC_IDS", "RFO_FIXED_TIME", "RFO_NO_NETWORK", "RFO_ID_SALT"):
        env.pop(_drop, None)
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

    pcr = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_corrupt_render.py")], env, 300)
    steps.append(_step_tail("_smoke_corrupt_render", pcr))

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

    smoke_root_cli = Path(tempfile.mkdtemp(prefix="rfo-release-smoke-cli-"))
    env_cli = {**env, "RFO_V19_PROFILE": "mvr"}
    p_cli = _run(
        py,
        [py, "-S", core, "smoke", "--runs-root", str(smoke_root_cli), "--provider", "cli", "--interface", "direct_runtime"],
        env_cli,
        600,
    )
    smoke_report_cli = smoke_root_cli / "smoke-test-report.json"
    run_dir_cli = _smoke_run_dir(smoke_root_cli)
    extra_cli: dict[str, object] = {
        "smoke_report_sha256": _sha256_file(smoke_report_cli) if smoke_report_cli.is_file() else "",
        "smoke_run_dir": run_dir_cli,
    }
    eff_rc_cli = p_cli.returncode
    if p_cli.returncode == 0 and run_dir_cli:
        ok_c, note_c = _v19_post_smoke_ok(run_dir_cli)
        if not ok_c:
            eff_rc_cli = 1
            extra_cli["v19_closure_error"] = note_c
    extra_cli["rc_effective"] = eff_rc_cli
    row_cli = _step_tail("smoke_cli_v19", p_cli, extra_cli)
    row_cli["rc"] = eff_rc_cli
    steps.append(row_cli)

    p4 = _run(py, [py, "-S", core, "failure"], env, 600)
    steps.append(_step_tail("failure_corpus", p4))

    pv19 = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_fixture_suite.py"), "--verbose"], env, 600)
    steps.append(_step_tail("validate_v19_fixture_suite", pv19))

    pdr = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_deterministic_replay.py")], env, 600)
    steps.append(_step_tail("_smoke_deterministic_replay", pdr))

    ptrj = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_trajectory_v19.py")], env, 300)
    steps.append(_step_tail("_smoke_trajectory_v19", ptrj))

    pcov = _run(
        py,
        [py, "-S", str(ROOT / "scripts" / "validate_validator_coverage.py"), "--out", str(ROOT / "coverage-report.json")],
        env,
        600,
    )
    steps.append(_step_tail("coverage_meta", pcov))

    z_rc, z_extra = _build_release_zip_triad(ROOT)
    steps.append(_step_tail("release_zip_triad", _SP(z_rc, json.dumps(z_extra, ensure_ascii=False), "")))

    pci = _run(py, [py, "-S", str(ROOT / "scripts" / "_smoke_clean_install.py")], env, 900)
    steps.append(_step_tail("_smoke_clean_install", pci))

    prb = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_release_bad_suite.py")], env, 120)
    steps.append(_step_tail("validate_v19_release_bad_suite", prb))

    run_dir_nd = run_dir_v18 or run_dir_v19 or run_dir_cli
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
        "version": skill_ver or "19.1.0",
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
    for d in (smoke_root_v18, smoke_root_v19, smoke_root_cli):
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
