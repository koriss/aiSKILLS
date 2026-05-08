"""CLI entrypoint for RFO v19 runtime (adapter, execute, run, worker, outbox, validate, failure)."""
from __future__ import annotations

import argparse
import sys

from runtime.adapter_impl import cmd_adapter
from runtime.failure_impl import cmd_failure
from runtime.outbox_impl import cmd_outbox
from runtime.validate_impl import validate
from runtime.artifact_execute_impl import cmd_execute
from runtime.worker_impl import cmd_run, cmd_worker


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("adapter")
    s.add_argument("--runs-root", required=True)
    s.add_argument("--interface", default="cli")
    s.add_argument("--provider", default="cli")
    s.add_argument("--conversation-id", default="")
    s.add_argument("--message-id", default="")
    s.add_argument("--user-id", default="")
    s.add_argument("--task", default="")
    s.add_argument("--reply-text", default="")
    # Optional routing hints for whichever host adapter records them in interface-request.json;
    # the skill does not perform outbound messaging to external channels.
    s.add_argument("--chat-id", default="")
    s.add_argument("--reply-to-message-id", default="")
    s.add_argument("--api-base", default="")
    s = sub.add_parser("execute")
    s.add_argument("--runs-root", required=True)
    s.add_argument("--task", required=True)
    s.add_argument(
        "--profile",
        default="",
        help="Sets RFO_RUN_PROFILE for this run (mvr | full-rigor | source-packet). Empty: env/default.",
    )
    s.add_argument(
        "--seed-urls",
        default="",
        help="Comma-separated URLs for RFO_SEED_URLS (stdlib HEAD probes).",
    )
    s.add_argument(
        "--mode",
        default="research",
        help="Canonical run mode (research|production); passed to nested runtime run.",
    )
    s = sub.add_parser("run")
    s.add_argument("--project-dir", required=True)
    s.add_argument("--task", required=True)
    s.add_argument(
        "--mode",
        default="research",
        help="Canonical run mode after normalization (research|production); aliases e.g. AUTO_COMPILE_AND_EXECUTE map to research.",
    )
    s.add_argument("--run-id")
    s.add_argument("--job-id")
    s.add_argument("--command-id")
    s.add_argument("--provider", default="cli")
    s.add_argument("--interface", default="direct_runtime")
    s.add_argument(
        "--runs-root",
        default="",
        help="Optional runs root for honesty metadata (artifact execute path sets this).",
    )
    s = sub.add_parser("worker")
    s.add_argument("--runs-root", required=True)
    s.add_argument(
        "--mode",
        default="research",
        choices=("research", "production"),
        help="Propagated to nested run --mode (canonical).",
    )
    s.add_argument("--execute-runtime", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("outbox")
    s.add_argument("--runs-root", required=True)
    s = sub.add_parser("validate")
    s.add_argument("--run-dir", required=True)
    sub.add_parser("failure")
    a = p.parse_args()
    return {
        "adapter": cmd_adapter,
        "execute": cmd_execute,
        "run": cmd_run,
        "worker": cmd_worker,
        "outbox": cmd_outbox,
        "validate": lambda x: validate(x.run_dir),
        "failure": cmd_failure,
    }[a.cmd](a) or 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["main"]
