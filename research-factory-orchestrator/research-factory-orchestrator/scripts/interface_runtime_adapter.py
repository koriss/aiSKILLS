#!/usr/bin/env python3
"""RFO v19.2.x interface runtime adapter (canonical public entry).

This is the only canonical script for the bot to call. It hard-guards:

* the calling skill path (must be canonical
  ``research-factory-orchestrator`` under ``skills/`` or the source-repo
  nested layout); ``*.bak``/``*.old``/``*.disabled`` are rejected with
  exit code ``11`` and stderr stamp ``RFO-NON-CANONICAL-SKILL-PATH``.
* the ``--runs-root`` value (must be under
  ``$HOME/.openclaw/workspace/rfo-runs`` or ``$RFO_RUNS_ROOT``; ``/tmp``
  is permitted only with ``RFO_ALLOW_TMP_RUNS_ROOT=1`` consent). On
  violation: exit code ``12`` and stamp ``RFO-RUNS-ROOT-FORBIDDEN``.

Optional flags ``--chat-id``, ``--reply-to-message-id``, and ``--api-base`` are
recorded verbatim into ``interface/interface-request.json`` under
``delivery.*`` for the host process only. This skill computes artifacts and
local outbox stubs; any real user-visible send happens outside this repository.

Backwards compatible with v19.2.0: if invoked without an explicit
sub-command word, dispatches to ``adapter`` (legacy behaviour).
"""
from __future__ import annotations

import sys
from pathlib import Path

_SUBCOMMANDS = (
    "adapter",
    "execute",
    "run",
    "worker",
    "outbox",
    "validate",
    "failure",
)


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

    incoming = sys.argv[1:]
    if incoming and incoming[0] in _SUBCOMMANDS:
        new_argv = incoming
    else:
        # Legacy: implicit `adapter` sub-command.
        new_argv = ["adapter"] + incoming

    enforce_runs_root_argv(new_argv)

    sys.argv = [sys.argv[0]] + new_argv
    from runtime.cli import main as _cli_main

    return _cli_main() or 0


if __name__ == "__main__":
    raise SystemExit(main())
