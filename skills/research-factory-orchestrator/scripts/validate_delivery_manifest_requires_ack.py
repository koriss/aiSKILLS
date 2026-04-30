#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED_EVENTS = ["OUT-0001", "OUT-0002", "OUT-0003"]

def jread(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); args = ap.parse_args()
    root = Path(args.run_dir); errors = []
    for rel in ["delivery-manifest.json", "final-answer-gate.json", "attachment-ledger.json"]:
        if not (root/rel).exists(): errors.append("missing " + rel)
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    manifest = jread(root/"delivery-manifest.json"); gate = jread(root/"final-answer-gate.json"); attachment = jread(root/"attachment-ledger.json")
    required = manifest.get("required_outbox_events") or REQUIRED_EVENTS
    if manifest.get("local_paths_exposed"): errors.append("delivery-manifest local_paths_exposed=true")
    if manifest.get("required_acks_present") is not True: errors.append("required_acks_present is not true")
    if manifest.get("required_acks_missing"): errors.append("required_acks_missing is not empty")
    if manifest.get("delivery_proof_errors"): errors.append("delivery_proof_errors is not empty")
    for event_id in required:
        evp = root/"outbox"/f"{event_id}.json"; ackp = root/"delivery-acks"/f"{event_id}.json"
        if not evp.exists(): errors.append(f"missing outbox event {event_id}"); continue
        if not ackp.exists(): errors.append(f"missing delivery ack {event_id}"); continue
        ev = jread(evp); ack = jread(ackp)
        if ev.get("status") != "sent": errors.append(f"{event_id}: event not marked sent")
        for key in ["ack_id", "event_id", "run_id", "provider", "status", "idempotency_key", "created_at", "stub_delivery", "real_external_delivery"]:
            if key not in ack: errors.append(f"{event_id}: ack missing {key}")
        if ack.get("status") not in ["sent", "duplicate"]: errors.append(f"{event_id}: ack status invalid for terminal provider ACK")
        if ack.get("idempotency_key") != ev.get("idempotency_key"): errors.append(f"{event_id}: idempotency_key mismatch")
        if ack.get("stub_delivery") is True and ack.get("real_external_delivery") is True: errors.append(f"{event_id}: ack cannot be both stub and real external")
    gates = manifest.get("gates") or {}
    if (gates.get("provider_ack_gate") or {}).get("status") != "pass": errors.append("provider_ack_gate is not pass")
    if attachment.get("all_required_acknowledged") is not True and attachment.get("all_required_sent") is not True: errors.append("attachment-ledger required attachments not acknowledged")
    if manifest.get("delivery_status") == "stub_delivered":
        if gate.get("passed") is not False: errors.append("stub_delivered must not set final-answer-gate.passed=true")
        if gate.get("external_delivery_gate") != "stub_only": errors.append("stub external_delivery_gate must be stub_only")
        if gate.get("final_user_claim_gate") != "stub_only": errors.append("stub final_user_claim_gate must be stub_only")
        if manifest.get("delivery_claim_allowed") is not False: errors.append("stub delivery must not allow external delivery claim")
    elif manifest.get("delivery_status") == "delivered":
        if gate.get("passed") is not True: errors.append("real delivered must set final-answer-gate.passed=true")
        if gate.get("external_delivery_gate") != "pass": errors.append("real delivered external_delivery_gate must pass")
    else:
        errors.append(f"delivery_status is not terminal delivered/stub_delivered: {manifest.get('delivery_status')}")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: delivery manifest has ACK proof and v17.2 gate semantics"); return 0
if __name__ == "__main__": raise SystemExit(main())
