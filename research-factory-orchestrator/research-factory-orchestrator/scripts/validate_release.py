#!/usr/bin/env python3
"""Unified release verification: skill validation, schema drift, smoke, failure corpus, negative validators."""
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


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _sha256_obj(o: object) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    out_path = ROOT / "release-validation-transcript.json"
    steps = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable

    p = subprocess.run([py, "-S", str(ROOT / "scripts" / "validate_skill.py")], cwd=str(ROOT), capture_output=True, text=True, timeout=600, env=env)
    steps.append({"name": "validate_skill", "rc": p.returncode, "stdout_tail": (p.stdout or "")[-4000:], "stderr_tail": (p.stderr or "")[-2000:]})

    p2 = subprocess.run([py, "-S", str(ROOT / "scripts" / "check_schema_drift.py")], cwd=str(ROOT), capture_output=True, text=True, timeout=120, env=env)
    steps.append({"name": "check_schema_drift", "rc": p2.returncode, "stdout_tail": (p2.stdout or "")[-4000:], "stderr_tail": (p2.stderr or "")[-2000:]})

    smoke_root = tempfile.mkdtemp(prefix="rfo-release-smoke-")
    core = str(ROOT / "scripts" / "rfo_v18_core.py")

    p3 = subprocess.run(
        [py, "-S", core, "smoke", "--runs-root", smoke_root, "--provider", "telegram", "--interface", "telegram"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    smoke_report = Path(smoke_root) / "smoke-test-report.json"
    smoke_sha = _sha256_file(smoke_report) if smoke_report.is_file() else ""
    latest_path = Path(smoke_root) / "index" / "latest.json"
    run_dir = ""
    if latest_path.is_file():
        run_dir = str(json.loads(latest_path.read_text(encoding="utf-8")).get("run_dir") or "")
    steps.append(
        {
            "name": "smoke_telegram",
            "rc": p3.returncode,
            "smoke_report_sha256": smoke_sha,
            "smoke_run_dir": run_dir,
            "stdout_tail": (p3.stdout or "")[-4000:],
        }
    )

    p4 = subprocess.run([py, "-S", core, "failure"], cwd=str(ROOT), capture_output=True, text=True, timeout=600, env=env)
    steps.append({"name": "failure_corpus", "rc": p4.returncode, "stdout_tail": (p4.stdout or "")[-8000:], "stderr_tail": (p4.stderr or "")[-2000:]})

    v19_good = ROOT / "tests" / "fixtures" / "v19" / "good" / "mvr_minimal_valid"
    v19_rc = 0
    v19_tmp = Path(tempfile.mkdtemp(prefix="rfo-v19-good-"))
    try:
        if v19_good.is_dir():
            for item in v19_good.iterdir():
                dest = v19_tmp / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    shutil.copytree(item, dest)
            pv = subprocess.run(
                [py, "-S", str(ROOT / "scripts" / "run_core_validators.py"), "--run-dir", str(v19_tmp), "--profile", "mvr"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
            pc = subprocess.run(
                [py, "-S", str(ROOT / "scripts" / "check_validation_pass.py"), "--run-dir", str(v19_tmp)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            v19_rc = 0 if pv.returncode == 0 and pc.returncode == 0 else 1
            steps.append(
                {
                    "name": "v19_core_validators_good_fixture",
                    "rc": v19_rc,
                    "stdout_tail": ((pv.stdout or "") + "\n" + (pc.stdout or ""))[-4000:],
                    "stderr_tail": ((pv.stderr or "") + "\n" + (pc.stderr or ""))[-2000:],
                }
            )
        else:
            v19_rc = 1
            steps.append({"name": "v19_core_validators_good_fixture", "rc": 1, "error": "missing tests/fixtures/v19/good/mvr_minimal_valid"})
    finally:
        shutil.rmtree(v19_tmp, ignore_errors=True)

    nd_rc = 0
    if run_dir and Path(run_dir).is_dir():
        p5 = subprocess.run(
            [py, "-S", str(ROOT / "scripts" / "validate_no_delivery_after_validation_fail.py"), run_dir],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        nd_rc = p5.returncode
        steps.append({"name": "validate_no_delivery_after_validation_fail", "rc": nd_rc, "run_dir": run_dir})
    else:
        steps.append({"name": "validate_no_delivery_after_validation_fail", "rc": 1, "error": "no smoke run_dir"})

    skill_ver = ""
    try:
        vf = ROOT / "runtime" / "version.json"
        skill_ver = json.loads(vf.read_text(encoding="utf-8")).get("skill_version", "")
    except Exception:
        pass

    transcript = {
        "skill_version": skill_ver,
        "steps": steps,
        "transcript_sha256": "",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lc_rc = 0
    if run_dir and Path(run_dir).is_dir():
        p_lc = subprocess.run(
            [
                py,
                "-S",
                str(ROOT / "scripts" / "validate_logical_consistency.py"),
                run_dir,
                "--transcript",
                str(out_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        lc_rc = p_lc.returncode
        steps.append({"name": "validate_logical_consistency", "rc": lc_rc, "run_dir": run_dir})
    else:
        steps.append({"name": "validate_logical_consistency", "rc": 1, "error": "no smoke run_dir"})

    transcript["steps"] = steps
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_arg = os.environ.get("RFO_RELEASE_REPORT_PATH", "").strip()
    cmd = [py, "-S", str(ROOT / "scripts" / "validate_release_report.py"), "--transcript", str(out_path)]
    if report_arg and Path(report_arg).is_file():
        cmd.append(report_arg)
    pr = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120, env=env)
    steps_rr = transcript["steps"] + [{"name": "validate_release_report", "rc": pr.returncode, "stdout_tail": (pr.stdout or "")[-2000:]}]
    transcript["steps"] = steps_rr
    transcript["transcript_sha256"] = _sha256_obj({k: v for k, v in transcript.items() if k != "transcript_sha256"})
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    must_ok = [
        "validate_skill",
        "check_schema_drift",
        "smoke_telegram",
        "failure_corpus",
        "v19_core_validators_good_fixture",
        "validate_no_delivery_after_validation_fail",
        "validate_logical_consistency",
        "validate_release_report",
    ]
    failed = any(next((s for s in transcript["steps"] if s.get("name") == n), {}).get("rc", 1) != 0 for n in must_ok)

    print(json.dumps({"status": "fail" if failed else "pass", "release_validation_transcript": str(out_path)}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
