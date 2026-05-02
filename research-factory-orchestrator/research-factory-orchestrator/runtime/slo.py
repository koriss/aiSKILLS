"""SLI rollups from trace.jsonl + events.jsonl (operator burn-rate inputs)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _lines(p: Path) -> list[str]:
    if not p.is_file():
        return []
    return [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]


def compute_slis(run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    trace_n = len(_lines(run_dir / "trace.jsonl"))
    ev_n = len(_lines(run_dir / "events.jsonl"))
    vt = json.loads((run_dir / "validation-transcript.json").read_text(encoding="utf-8")) if (run_dir / "validation-transcript.json").exists() else {}
    dm = json.loads((run_dir / "delivery-manifest.json").read_text(encoding="utf-8")) if (run_dir / "delivery-manifest.json").exists() else {}
    validators_pass = 1.0 if vt.get("status") == "pass" else 0.0
    delivery_ok = 1.0 if str(dm.get("delivery_status") or "") in ("delivered", "stub_delivered") else 0.0
    ev_lines = _lines(run_dir / "events.jsonl")
    eids: list[str | None] = []
    for ln in ev_lines:
        try:
            eids.append(json.loads(ln).get("event_id"))
        except Exception:
            eids.append(None)
    non_null = [e for e in eids if e]
    replay_det = 1.0 if not non_null else (1.0 if len(non_null) == len(set(non_null)) else 0.0)
    return {
        "validators_pass_rate": validators_pass,
        "delivery_success_rate": delivery_ok,
        "hallucination_detect_rate": 0.0,
        "replay_determinism_rate": replay_det,
        "injection_attempts_blocked_rate": 0.0,
        "trace_lines": trace_n,
        "event_lines": ev_n,
    }
