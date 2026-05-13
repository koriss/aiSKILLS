#!/usr/bin/env python3
"""Retired operator entrypoint — grave marker only.

Historically a standalone relay research driver; implementation was removed from this file.
Tests and tooling import helpers from ``runtime.standalone_relay_driver``.

Use::

  python3 -S scripts/rfo_execute.py --task \"…\" --web-search-json-api-base \"…\"

from the skill root (see SKILL.md, docs/runtime-paths.md).
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "[fatal] scripts/run_rfo_full_research.py is a legacy standalone entrypoint.\n"
        "Research is not started. Use the single operator CLI:\n"
        "  python3 -S scripts/rfo_execute.py --task \"…\" --web-search-json-api-base \"…\"\n"
        "Helpers for tests live in runtime.standalone_relay_driver (not this script).\n"
        "See SKILL.md and docs/runtime-paths.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
