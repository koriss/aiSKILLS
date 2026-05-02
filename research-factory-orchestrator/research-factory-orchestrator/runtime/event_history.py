"""Append-only side-effect log for deterministic replay (Temporal-style event sourcing)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _h(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def append_side_effect(run_dir: Path, command_type: str, payload: dict[str, Any], result: dict[str, Any] | None = None) -> None:
    run_dir = Path(run_dir)
    p = run_dir / "events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    ph = _h(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    rh = _h(json.dumps(result or {}, sort_keys=True, ensure_ascii=False))
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    eid = "EVT-" + _h(command_type + ph + ts)[:12]
    rec = {
        "event_id": eid,
        "command_type": command_type,
        "payload_hash": ph,
        "result_hash": rh,
        "ts": ts,
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
