"""Deprecated: legacy aggregator. Use runtime.cli and runtime.*_impl directly."""
from __future__ import annotations

from runtime.adapter_impl import cmd_adapter
from runtime.cli import main
from runtime.failure_impl import cmd_failure
from runtime.outbox_impl import cmd_outbox
from runtime.smoke_impl import cmd_smoke
from runtime.validate_impl import validate
from runtime.worker_impl import cmd_run, cmd_worker

__all__ = ["main", "cmd_adapter", "cmd_run", "cmd_worker", "cmd_outbox", "validate", "cmd_smoke", "cmd_failure"]
