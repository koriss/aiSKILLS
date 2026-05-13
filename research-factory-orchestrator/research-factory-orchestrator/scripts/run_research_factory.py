#!/usr/bin/env python3
"""Deprecated operator CLI shim.

The queue worker invokes ``scripts/rfo_runtime_core.py`` directly. This file is
kept for provenance strings in contracts and validators — **do not** run it as
your entrypoint for research.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "[fatal] scripts/run_research_factory.py is not a supported operator entrypoint.\n"
        "Use:\n"
        "  python3 -S scripts/rfo_execute.py --task \"…\" --web-search-json-api-base \"…\"\n"
        "from the skill root (set OPENCLAW_WORKSPACE_DIR or pass --workspace-root / --runs-root).\n"
        "Internal worker runtime uses scripts/rfo_runtime_core.py (not this file).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
