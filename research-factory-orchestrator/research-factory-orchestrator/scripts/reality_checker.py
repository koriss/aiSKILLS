#!/usr/bin/env python3
"""Final publication gate: default NEEDS_WORK; READY only with overwhelming evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    args = ap.parse_args()
    rd = args.run_dir
    fg = json.loads((rd / "final-answer-gate.json").read_text(encoding="utf-8")) if (rd / "final-answer-gate.json").exists() else {}
    dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8")) if (rd / "delivery-manifest.json").exists() else {}
    vt = json.loads((rd / "validation-transcript.json").read_text(encoding="utf-8")) if (rd / "validation-transcript.json").exists() else {}
    gates = fg.get("gates") or {}
    need = [
        "provider_ack_gate",
        "external_delivery_gate",
        "content_gate",
        "package_gate",
        "citation_grounding_gate",
        "run_mode_gate",
        "intent_alignment_gate",
        "capability_gate",
        "replay_determinism_gate",
        "trace_chain_gate",
        "cross_model_judge_gate",
    ]
    gates_present = all(g in gates for g in need)
    gates_ok = gates_present and all(gates.get(g, {}).get("passed") for g in need)
    validators_ok = vt.get("status") == "pass"
    delivery_sent = dm.get("delivery_status") in ("sent", "delivered", "stub_delivered")
    evidence_pack = (rd / "evidence-pack").is_dir() or (rd / "delivery-acks").is_dir()
    if fg.get("passed") and validators_ok and delivery_sent and gates_ok and evidence_pack:
        verdict = "READY"
    elif vt.get("status") != "pass":
        verdict = "NOT_READY"
    else:
        verdict = "NEEDS_WORK"
    out = {
        "verdict": verdict,
        "validators_ok": validators_ok,
        "delivery_status": dm.get("delivery_status"),
        "gates_present": gates_present,
        "gates_ok": gates_ok,
    }
    (rd / "self-audit").mkdir(parents=True, exist_ok=True)
    (rd / "self-audit" / "reality-checker.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", **out}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
