#!/usr/bin/env python3
"""Canonical RFO runtime CLI funnel (v19.2.x). Implementation: ``runtime.cli.main``.

Defense-in-depth honesty hardening (v19.2.1): even when this script is
invoked directly (bypassing ``interface_runtime_adapter.py`` /
``runtime_job_worker.py`` / ``outbox_delivery_worker.py``), the canonical
skill-path and approved ``--runs-root`` guards from
``scripts/_rfo_path_guard.py`` still fire first.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _rfo_path_guard import (  # noqa: E402  - imported after sys.path fixup
    enforce_canonical_skill_path,
    enforce_runs_root_argv,
)

enforce_canonical_skill_path(__file__)
enforce_runs_root_argv(sys.argv[1:])

from runtime.status import VERSION  # noqa: E402
from runtime.util import now, jw      # noqa: E402
from runtime.cli import main          # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
