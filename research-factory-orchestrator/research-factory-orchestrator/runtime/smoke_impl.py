"""End-to-end smoke: adapter → worker → outbox → validate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime.util import jr, jw, now, skill_root
from runtime.status import VERSION


def cmd_smoke(a):
    root = Path(a.runs_root or tempfile.mkdtemp(prefix="rfo-v18-smoke-"))
    root.mkdir(parents=True, exist_ok=True)
    rep = {"smoke_test_version": VERSION, "runs_root": str(root), "steps": [], "report_path": str(root / "smoke-test-report.json"), "started_at": now()}

    def step(name, cmd):
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=240, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        rep["steps"].append({"name": name, "returncode": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]})
        jw(rep["report_path"], rep)
        if p.returncode:
            raise RuntimeError(name + " failed")

    core = str(skill_root() / "scripts" / "rfo_v18_core.py")
    py = sys.executable
    step("adapter", [py, "-S", core, "adapter", "--runs-root", str(root), "--interface", a.interface, "--provider", a.provider, "--conversation-id", a.conversation_id, "--message-id", a.message_id, "--user-id", a.user_id, "--task", a.task])
    step("worker", [py, "-S", core, "worker", "--runs-root", str(root), "--mode", "research", "--execute-runtime"])
    step("outbox", [py, "-S", core, "outbox", "--runs-root", str(root)])
    latest = jr(root / "index/latest.json")
    rd = Path(latest["run_dir"])
    step("validate", [py, "-S", core, "validate", "--run-dir", str(rd)])
    gate = jr(rd / "final-answer-gate.json")
    rep.update({"smoke_test_passed": True, "run_dir": str(rd), "run_id": latest["run_id"], "run_label": latest["run_label"], "final_answer_gate": gate, "finished_at": now()})
    jw(rep["report_path"], rep)
    print(json.dumps({"smoke_test_passed": True, "runs_root": str(root), "run_dir": str(rd), "final_gate_status": gate.get("status")}, ensure_ascii=False, indent=2))
