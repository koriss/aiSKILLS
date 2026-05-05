"""End-to-end smoke: adapter → worker → outbox → validate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime.util import jr, jw, now, skill_root
from runtime import util as util_mod
from runtime.status import VERSION
from runtime.validate_impl import V19_PROFILES


def _v19_rollback_closure_ok(rd: Path) -> bool:
    """J5: validate may return non-zero under v19 profile; smoke still passes if rollback is complete."""
    dm = jr(rd / "delivery-manifest.json", {})
    fg = jr(rd / "final-answer-gate.json", {})
    rs = jr(rd / "runtime-status.json", {})
    tr = jr(rd / "validation-transcript.json", {})
    if not isinstance(dm, dict) or not isinstance(fg, dict) or not isinstance(rs, dict):
        return False
    if dm.get("delivery_status") != "validation_failed":
        return False
    if not (dm.get("real_external_delivery") is False and dm.get("external_delivery_claim_allowed") is False):
        return False
    if fg.get("passed") is not False or fg.get("status") != "fail":
        return False
    if rs.get("state") != "validation_failed":
        return False
    if not isinstance(tr, dict):
        return False
    if tr.get("overall_pass") is True:
        return False
    if tr.get("overall_pass") is False:
        return True
    return False


def cmd_smoke(a):
    root = Path(a.runs_root or tempfile.mkdtemp(prefix="rfo-v18-smoke-"))
    root.mkdir(parents=True, exist_ok=True)
    rep = {"smoke_test_version": VERSION, "runs_root": str(root), "steps": [], "report_path": str(root / "smoke-test-report.json"), "started_at": now()}

    def step(name, cmd):
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        rep["steps"].append({"name": name, "returncode": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]})
        jw(rep["report_path"], rep)
        if p.returncode:
            raise RuntimeError(name + " failed")

    def step_validate_v19_aware(rd: Path, cmd: list[str]) -> None:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=240, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        prof = os.environ.get("RFO_V19_PROFILE", "").strip().lower()
        effective_rc = p.returncode
        note = ""
        if p.returncode != 0 and prof in V19_PROFILES and _v19_rollback_closure_ok(rd):
            effective_rc = 0
            note = "v19_validate_nonzero_but_rollback_closure_ok"
        entry = {
            "name": "validate",
            "returncode": p.returncode,
            "effective_returncode": effective_rc,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }
        if note:
            entry["note"] = note
        rep["steps"].append(entry)
        jw(rep["report_path"], rep)
        if effective_rc:
            raise RuntimeError("validate failed")

    def step_deterministic_smoke() -> None:
        """When ``RFO_FIXED_TIME`` is set, ``now()`` must be stable across calls (ADR-013)."""
        a = util_mod.now()
        b = util_mod.now()
        rep["steps"].append({"name": "deterministic_time_probe", "first": a, "second": b, "match": a == b})
        jw(rep["report_path"], rep)
        if os.environ.get("RFO_FIXED_TIME", "").strip() and a != b:
            raise RuntimeError("deterministic_time_probe: RFO_FIXED_TIME set but now() unstable")

    step_deterministic_smoke()

    core = str(skill_root() / "scripts" / "rfo_v18_core.py")
    py = sys.executable
    step("adapter", [py, "-S", core, "adapter", "--runs-root", str(root), "--interface", a.interface, "--provider", a.provider, "--conversation-id", a.conversation_id, "--message-id", a.message_id, "--user-id", a.user_id, "--task", a.task])
    step("worker", [py, "-S", core, "worker", "--runs-root", str(root), "--mode", "research", "--execute-runtime"])
    step("outbox", [py, "-S", core, "outbox", "--runs-root", str(root)])
    latest = jr(root / "index/latest.json")
    rd = Path(latest["run_dir"])
    step_validate_v19_aware(rd, [py, "-S", core, "validate", "--run-dir", str(rd)])
    gate = jr(rd / "final-answer-gate.json")
    rep.update({"smoke_test_passed": True, "run_dir": str(rd), "run_id": latest["run_id"], "run_label": latest["run_label"], "final_answer_gate": gate, "finished_at": now()})
    jw(rep["report_path"], rep)
    print(json.dumps({"smoke_test_passed": True, "runs_root": str(root), "run_dir": str(rd), "final_gate_status": gate.get("status")}, ensure_ascii=False, indent=2))
