#!/usr/bin/env python3
"""Compatibility entrypoint → ``verify_skill_run_claims`` (canonical).

Historical name kept on disk so existing operator docs and shells keep working.
JSON output reports ``validator_id``: **verify_skill_run_claims** — update any
automated consumers that keyed on ``verify_openclaw_run``.
"""
from __future__ import annotations

import sys
from pathlib import Path

_scripts = Path(__file__).resolve().parent
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

from verify_skill_run_claims import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
