#!/usr/bin/env python3
"""Parallel `execute` smokes: distinct run_dir per marker (RFO v19.3)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "interface_runtime_adapter.py"
MARKER = "__OPENCLAW_SKILL_RESULT__="


def _parse_marker(stdout: str) -> dict:
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines or not lines[-1].startswith(MARKER):
        raise RuntimeError("missing marker line")
    return json.loads(lines[-1][len(MARKER) :])


def _run_one(idx: int, runs_root: Path) -> str:
    env = {**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1"}
    task = f"v19.3 concurrency probe {idx}"
    cmd = [
        sys.executable or "python3",
        "-S",
        str(ADAPTER),
        "execute",
        "--task",
        task,
        "--runs-root",
        str(runs_root),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), env=env, timeout=900)
    if p.returncode not in (0, 10):
        raise RuntimeError(f"exit {p.returncode} stderr={p.stderr[:800]!r}")
    m = _parse_marker(p.stdout)
    rd = str(m.get("run_dir") or "")
    if not rd:
        raise RuntimeError("marker missing run_dir")
    return rd


def main() -> int:
    if not ADAPTER.is_file():
        print("missing adapter", ADAPTER, file=sys.stderr)
        return 2
    runs_root = Path(tempfile.mkdtemp(prefix="rfo-v19-3-concurrency-"))
    dirs: list[str] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_run_one, i, runs_root): i for i in range(3)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                dirs.append(fut.result())
            except Exception as e:
                errors.append(f"worker {i}: {e!r}")
    if errors:
        print(json.dumps({"passed": False, "errors": errors}, indent=2))
        return 1
    if len(set(dirs)) != len(dirs):
        print(json.dumps({"passed": False, "errors": ["duplicate run_dir in markers"], "run_dirs": dirs}, indent=2))
        return 1
    print(json.dumps({"passed": True, "run_dirs": dirs, "runs_root": str(runs_root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
