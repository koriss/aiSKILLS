"""Tamper-evident trace.jsonl chain (prev_hash per line; RFC 9162 / audit log patterns)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canon(obj: dict[str, Any]) -> str:
    d = {k: v for k, v in obj.items() if k != "record_hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def append_trace_line(run_dir: Path, payload: dict[str, Any]) -> None:
    p = Path(run_dir) / "trace.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    prev = GENESIS
    if p.exists() and p.stat().st_size > 0:
        lines = p.read_text(encoding="utf-8").splitlines()
        if lines:
            prev = hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
    rec = {**payload, "prev_hash": prev}
    rec["record_hash"] = hashlib.sha256(_canon(rec).encode("utf-8")).hexdigest()
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
