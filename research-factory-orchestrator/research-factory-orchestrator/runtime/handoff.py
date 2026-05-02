"""Phase-to-phase handoff envelopes (AgentAsk edge taxonomy; SCF pre-execution alignment)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.status import VERSION


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _genesis() -> str:
    return "0" * 64


def _prev_chain_hash(run_dir: Path) -> str:
    d = run_dir / "handoffs"
    if not d.is_dir():
        return _genesis()
    files = sorted(d.glob("HOFF-*.json"))
    if not files:
        return _genesis()
    raw = files[-1].read_text(encoding="utf-8")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def emit_handoff(
    run_dir: Path,
    from_phase: str,
    to_phase: str,
    payload: dict[str, Any],
    *,
    required_fields: list[str] | None = None,
    timeout_ms: int = 120_000,
    on_failure_action: str = "block",
) -> Path:
    """Write HOFF-{ts}-{from}-to-{to}.json under run-dir/handoffs/ with tamper-evident prev_hash."""
    run_dir = Path(run_dir)
    hd = run_dir / "handoffs"
    hd.mkdir(parents=True, exist_ok=True)
    prev_hash = _prev_chain_hash(run_dir)
    req = required_fields or ["run_id", "job_id"]
    ph = hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()
    ts = _now_iso().replace(":", "").replace("-", "")[:15]
    safe_from = re.sub(r"[^a-z0-9_]+", "_", from_phase.lower()).strip("_") or "from"
    safe_to = re.sub(r"[^a-z0-9_]+", "_", to_phase.lower()).strip("_") or "to"
    fname = f"HOFF-{ts}-{safe_from}-to-{safe_to}.json"
    handoff_id = f"HOFF-{ph[:12]}"
    envelope: dict[str, Any] = {
        "handoff_id": handoff_id,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "payload_hash": ph,
        "required_fields": req,
        "success_response": "ACK",
        "failure_response": "NACK",
        "timeout_ms": timeout_ms,
        "on_failure_action": on_failure_action,
        "prev_hash": prev_hash,
        "created_at": _now_iso(),
        "payload": payload,
        "skill_version": VERSION,
    }
    out = hd / fname
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
