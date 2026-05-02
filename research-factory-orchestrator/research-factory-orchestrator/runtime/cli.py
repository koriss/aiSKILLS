"""CLI entrypoint for RFO v18 runtime (subcommands: adapter, run, worker, outbox, validate, smoke, failure)."""
from __future__ import annotations

import argparse
import sys

from runtime.adapter_impl import cmd_adapter
from runtime.failure_impl import cmd_failure
from runtime.outbox_impl import cmd_outbox
from runtime.smoke_impl import cmd_smoke
from runtime.validate_impl import validate
from runtime.worker_impl import cmd_run, cmd_worker


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("adapter")
    s.add_argument("--runs-root", required=True)
    s.add_argument("--interface", default="telegram")
    s.add_argument("--provider", default="telegram")
    s.add_argument("--conversation-id", default="")
    s.add_argument("--message-id", default="")
    s.add_argument("--user-id", default="")
    s.add_argument("--task", default="")
    s.add_argument("--reply-text", default="")
    s = sub.add_parser("run")
    s.add_argument("--project-dir", required=True)
    s.add_argument("--task", required=True)
    s.add_argument(
        "--mode",
        default="research",
        help="Canonical run mode after normalization (research|production|smoke); aliases e.g. AUTO_COMPILE_AND_EXECUTE map to research.",
    )
    s.add_argument("--run-id")
    s.add_argument("--job-id")
    s.add_argument("--command-id")
    s.add_argument("--provider", default="cli")
    s.add_argument("--interface", default="direct_runtime")
    s = sub.add_parser("worker")
    s.add_argument("--runs-root", required=True)
    s.add_argument(
        "--mode",
        default="research",
        choices=("research", "production", "smoke"),
        help="Propagated to nested run --mode (canonical).",
    )
    s.add_argument("--execute-runtime", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("outbox")
    s.add_argument("--runs-root", required=True)
    s = sub.add_parser("validate")
    s.add_argument("--run-dir", required=True)
    s = sub.add_parser("smoke")
    s.add_argument("--provider", default="telegram")
    s.add_argument("--interface", default="telegram")
    s.add_argument("--conversation-id", default="test")
    s.add_argument("--message-id", default="1")
    s.add_argument("--user-id", default="me")
    s.add_argument("--task", default="test internal audit target")
    s.add_argument("--runs-root")
    sub.add_parser("failure")
    a = p.parse_args()
    return {
        "adapter": cmd_adapter,
        "run": cmd_run,
        "worker": cmd_worker,
        "outbox": cmd_outbox,
        "validate": lambda x: validate(x.run_dir),
        "smoke": cmd_smoke,
        "failure": cmd_failure,
    }[a.cmd](a) or 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["main"]
