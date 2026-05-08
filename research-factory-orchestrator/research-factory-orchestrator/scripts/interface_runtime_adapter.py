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

It accepts new optional delivery flags introduced in v19.2.1:

  ``--chat-id``               Telegram chat_id from the *incoming* update.
                              Required for real (non-stub) delivery.
  ``--reply-to-message-id``   message_id of the user's incoming message,
                              used as ``reply_to_message_id`` on send.
  ``--api-base``              Telegram Bot API base URL (default
                              ``https://api.telegram.org``); also taken
                              from ``TELEGRAM_API_BASE`` if not provided.

These are persisted into ``interface/interface-request.json`` under
``delivery.chat_id``, ``delivery.reply_to_message_id`` and
``delivery.api_base`` respectively, where the Telegram delivery adapter
picks them up at outbox time (see ``providers/telegram/telegram_delivery_adapter.py``).

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
    "smoke",
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
