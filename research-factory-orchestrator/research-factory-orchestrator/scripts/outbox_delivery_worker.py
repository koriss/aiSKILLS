#!/usr/bin/env python3
"""Recompute delivery-manifest / final-answer-gate for a single run directory."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def recompute_delivery_state(run_dir: Path) -> None:
    run_dir = Path(run_dir).resolve()
    runs_root = run_dir.parent.parent
    core = Path(__file__).resolve().parent / "rfo_v18_core.py"
    r = subprocess.run(
        [sys.executable, "-S", str(core), "outbox", "--runs-root", str(runs_root)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(
            "outbox failed: "
            + (r.stderr or r.stdout or str(r.returncode))
        )


def main() -> None:
    core = Path(__file__).resolve().parent / "rfo_v18_core.py"
    sys.argv = [str(core), "outbox"] + sys.argv[1:]
    import runpy

    runpy.run_path(str(core), run_name="__main__")


if __name__ == "__main__":
    main()
