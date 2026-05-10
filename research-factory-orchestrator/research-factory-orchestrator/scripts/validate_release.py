#!/usr/bin/env python3
"""Unified release verification: skill validation, schema drift, artifact execute gate, failure corpus, B4 self-attestation (v19.0.4+)."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import types
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
        "artifact_execute_v19_3",
        "validate_artifact_release",
        "failure_corpus",
        "validate_v19_fixture_suite",
        "validate_v19_release_bad_suite",
        "validate_active_contract_versions",
        "validate_profile_policies_present",
        "validate_advisory_fixture_suite",
        "coverage_meta",
        "release_zip_triad",
        "validate_no_delivery_after_validation_fail",
        "validate_no_scaffolds_in_production",
        "validate_no_failed_validation_in_production",
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
    """T8.1: ``Popen(start_new_session=True)`` + ``killpg`` on timeout to avoid zombie children."""
    if os.name != "nt":
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate(timeout=120)
            fake = types.SimpleNamespace(
                returncode=124,
                stdout=out or "",
                stderr=(err or "") + "\n[validate_release: subprocess killed after timeout]\n",
            )
            return fake  # type: ignore[return-value]
        fake2 = types.SimpleNamespace(returncode=proc.returncode, stdout=out or "", stderr=err or "")
        return fake2  # type: ignore[return-value]
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


def _latest_run_dir_from_runs_root(runs_root: Path) -> str:
    latest_path = runs_root / "index" / "latest.json"
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
        "debug-runs",
    }
)


def _build_release_zip_triad(root: Path) -> tuple[int, dict[str, object]]:
    """Stdlib zip + sha256 sidecar + release-manifest.json under ``release-artifacts/``."""
    extra: dict[str, object] = {}
    try:
        ver = str(json.loads((root / "runtime" / "version.json").read_text(encoding="utf-8")).get("skill_version", ""))
    except Exception:
        ver = "19.2.0"
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
        "schema_version": "v19.2",
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


def main() -> int:
    out_path = ROOT / "release-validation-transcript.json"
    steps: list[dict[str, object]] = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    # Isolate harness env from deterministic test knobs so release runs match production behavior.
    for _drop in ("RFO_DETERMINISTIC_IDS", "RFO_FIXED_TIME", "RFO_NO_NETWORK", "RFO_ID_SALT"):
        env.pop(_drop, None)
    py = sys.executable

    p = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_skill.py")], env, 600)
    steps.append(_step_tail("validate_skill", p))

    p2 = _run(py, [py, "-S", str(ROOT / "scripts" / "check_schema_drift.py")], env, 120)
    steps.append(_step_tail("check_schema_drift", p2))

    pa = _run(py, [py, "-S", str(ROOT / "scripts" / "_audit_composition_schemas.py")], env, 120)
    steps.append(_step_tail("_audit_composition_schemas", pa))

    core = str(ROOT / "scripts" / "rfo_runtime_core.py")
    artifact_execute_root = Path(tempfile.mkdtemp(prefix="rfo-release-execute-v19-3-"))
    env_ex = {**env, "RFO_ALLOW_TMP_RUNS_ROOT": "1"}
    pex = _run(
        py,
        [
            py,
            "-S",
            str(ROOT / "scripts" / "interface_runtime_adapter.py"),
            "execute",
            "--runs-root",
            str(artifact_execute_root),
            "--task",
            "release_gate_artifact_execute_v19_3",
        ],
        env_ex,
        600,
    )
    run_dir_execute = _latest_run_dir_from_runs_root(artifact_execute_root)
    steps.append(
        _step_tail(
            "artifact_execute_v19_3",
            pex,
            {"artifact_execute_run_dir": run_dir_execute},
        )
    )
    p_art_val = _SP(1, "", "no_run_dir")
    if run_dir_execute and Path(run_dir_execute).is_dir():
        p_art_val = _run(
            py,
            [py, "-S", str(ROOT / "scripts" / "validate_artifact_release.py"), "--run-dir", run_dir_execute],
            env,
            120,
        )
    steps.append(_step_tail("validate_artifact_release", p_art_val, {"run_dir": run_dir_execute}))

    p4 = _run(py, [py, "-S", core, "failure"], env, 600)
    steps.append(_step_tail("failure_corpus", p4))

    pv19 = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_fixture_suite.py"), "--verbose"], env, 600)
    steps.append(_step_tail("validate_v19_fixture_suite", pv19))

    pact = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_active_contract_versions.py")], env, 120)
    steps.append(_step_tail("validate_active_contract_versions", pact))

    ppol = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_profile_policies_present.py")], env, 120)
    steps.append(_step_tail("validate_profile_policies_present", ppol))

    padv = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_advisory_fixture_suite.py")], env, 120)
    steps.append(_step_tail("validate_advisory_fixture_suite", padv))

    pcov = _run(
        py,
        [py, "-S", str(ROOT / "scripts" / "validate_validator_coverage.py"), "--out", str(ROOT / "coverage-report.json")],
        env,
        600,
    )
    steps.append(_step_tail("coverage_meta", pcov))

    z_rc, z_extra = _build_release_zip_triad(ROOT)
    steps.append(_step_tail("release_zip_triad", _SP(z_rc, json.dumps(z_extra, ensure_ascii=False), "")))

    prb = _run(py, [py, "-S", str(ROOT / "scripts" / "validate_v19_release_bad_suite.py")], env, 120)
    steps.append(_step_tail("validate_v19_release_bad_suite", prb))

    run_dir_nd = run_dir_execute
    run_dir_prodish = run_dir_execute
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
        steps.append({"name": "validate_no_delivery_after_validation_fail", "rc": 1, "error": "no artifact_execute run_dir"})
    if run_dir_prodish and Path(run_dir_prodish).is_dir():
        pns = _run(
            py,
            [py, "-S", str(ROOT / "scripts" / "validate_no_scaffolds_in_production.py"), "--run-dir", run_dir_prodish],
            env,
            120,
        )
        steps.append(_step_tail("validate_no_scaffolds_in_production", pns, {"run_dir": run_dir_prodish}))
        pnf = _run(
            py,
            [py, "-S", str(ROOT / "scripts" / "validate_no_failed_validation_in_production.py"), "--run-dir", run_dir_prodish],
            env,
            120,
        )
        steps.append(_step_tail("validate_no_failed_validation_in_production", pnf, {"run_dir": run_dir_prodish}))
    else:
        steps.append({"name": "validate_no_scaffolds_in_production", "rc": 1, "error": "no artifact_execute run_dir"})
        steps.append({"name": "validate_no_failed_validation_in_production", "rc": 1, "error": "no artifact_execute run_dir"})

    skill_ver = ""
    try:
        vf = ROOT / "runtime" / "version.json"
        skill_ver = str(json.loads(vf.read_text(encoding="utf-8")).get("skill_version", ""))
    except Exception:
        pass

    transcript: dict[str, object] = {
        "version": skill_ver or "19.2.0",
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
        steps.append({"name": "validate_logical_consistency", "rc": 1, "error": "no artifact_execute run_dir"})

    transcript["steps"] = steps
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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

    # cleanup temp runs roots (best effort)
    for d in (artifact_execute_root,):
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
