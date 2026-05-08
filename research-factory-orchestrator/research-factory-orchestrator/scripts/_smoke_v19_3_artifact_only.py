#!/usr/bin/env python3
"""Smoke: artifact-only execute + manifest validation (v19.3)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    py = sys.executable
    d = Path(tempfile.mkdtemp(prefix="rfo-smoke-v19-3-"))
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "RFO_ALLOW_TMP_RUNS_ROOT": "1",
        "RFO_V19_PROFILE": "mvr",
    }
    cmd = [
        py,
        "-S",
        str(ROOT / "scripts" / "interface_runtime_adapter.py"),
        "execute",
        "--runs-root",
        str(d),
        "--task",
        "v19.3 artifact-only smoke task",
    ]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env, timeout=300)
    out = (p.stdout or "").strip().splitlines()
    marker = [ln for ln in out if ln.startswith("__OPENCLAW_SKILL_RESULT__=")]
    if p.returncode != 0 or not marker:
        sys.stderr.write(p.stderr or "")
        sys.stderr.write(p.stdout or "")
        print(json.dumps({"ok": False, "error": "execute_failed", "rc": p.returncode}, ensure_ascii=False))
        return 1
    payload = json.loads(marker[-1].split("=", 1)[1])
    rd = Path(payload["run_dir"])
    v = subprocess.run(
        [py, "-S", str(ROOT / "scripts" / "validate_artifact_release.py"), "--run-dir", str(rd)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    if v.returncode != 0:
        sys.stderr.write(v.stderr or "")
        sys.stderr.write(v.stdout or "")
        print(json.dumps({"ok": False, "error": "validate_artifact_failed"}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "run_dir": str(rd), "marker": payload}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
