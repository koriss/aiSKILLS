#!/usr/bin/env python3
"""RFO v19.2.x outbox delivery worker (canonical public entry).

Recomputes ``delivery-manifest.json`` / ``final-answer-gate.json`` for a
single run directory. Hard-guards canonical skill path and approved
``--runs-root`` (see ``scripts/_rfo_path_guard.py``) before delegating
to ``runtime.cli`` ``outbox`` sub-command. ``recompute_delivery_state``
is preserved for legacy callers (worker, validation harness).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _bootstrap_paths() -> Path:
    here = Path(__file__).resolve()
    skill_root = here.parent.parent
    scripts_dir = skill_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    return skill_root


def recompute_delivery_state(run_dir: Path) -> None:
    """Recompute delivery state for ``run_dir`` via subprocess (legacy API)."""
    run_dir = Path(run_dir).resolve()
    runs_root = run_dir.parent.parent
    skill_root = _bootstrap_paths()
    core = skill_root / "scripts" / "rfo_runtime_core.py"
    r = subprocess.run(
        [
            sys.executable,
            "-S",
            str(core),
            "outbox",
            "--runs-root",
            str(runs_root),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(
            "outbox failed: "
            + (r.stderr or r.stdout or str(r.returncode))
        )


def main() -> int:
    _bootstrap_paths()

    from _rfo_path_guard import (
        enforce_canonical_skill_path,
        enforce_runs_root_argv,
    )

    enforce_canonical_skill_path(__file__)
    new_argv = ["outbox"] + sys.argv[1:]
    enforce_runs_root_argv(new_argv)
    sys.argv = [sys.argv[0]] + new_argv

    from runtime.cli import main as _cli_main

    return _cli_main() or 0


if __name__ == "__main__":
    raise SystemExit(main())
