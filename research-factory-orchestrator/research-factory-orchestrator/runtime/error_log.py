"""Structured error log for runtime failures (RFO v19.2.0).

Closes runtime feedback hole observed in v18.5.1 cycle: ``.errors.log`` was
629 bytes for 10 RFO runs and missed every meaningful failure (delivery
stub_only, fetch errors, validation failures). This module appends one JSON
event per error/warning to ``runtime/errors.jsonl`` so validate_error_log_quality
can rank quality (kind variety, code coverage, severity mix).

stdlib-only, append-safe, never raises.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def append_error(rd: Path, *, code: str, severity: str, detail: str, context: dict | None = None) -> None:
    rd = Path(rd)
    log = rd / "runtime" / "errors.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "code": code,
        "severity": severity,
        "detail": detail,
        "context": context or {},
        "pid": os.getpid(),
    }
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        # Never fail the run because of an error-log write failure.
        pass
