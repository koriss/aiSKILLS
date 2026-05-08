#!/usr/bin/env python3
"""RFO v19.2.x runtime job worker (canonical public entry).

Hard-guards canonical skill path and approved ``--runs-root`` (see
``scripts/_rfo_path_guard.py`` for the full contract) before delegating
to ``runtime.cli`` ``worker`` sub-command. ``*.bak``/``*.old`` skill
copies and ``/tmp`` runs-roots without consent are rejected with stable
error stamps.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve()
    skill_root = here.parent.parent
    scripts_dir = skill_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))

    from _rfo_path_guard import (
        enforce_canonical_skill_path,
        enforce_runs_root_argv,
    )

    enforce_canonical_skill_path(__file__)
    new_argv = ["worker"] + sys.argv[1:]
    enforce_runs_root_argv(new_argv)
    sys.argv = [sys.argv[0]] + new_argv

    from runtime.cli import main as _cli_main

    return _cli_main() or 0


if __name__ == "__main__":
    raise SystemExit(main())
