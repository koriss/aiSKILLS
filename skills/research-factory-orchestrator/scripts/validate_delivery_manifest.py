#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

TERMINAL = {"delivered", "stub_delivered"}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("delivery_manifest"); args = ap.parse_args()
    d = json.loads(Path(args.delivery_manifest).read_text(encoding="utf-8")); errors = []
    status = d.get("delivery_status")
    gates = d.get("gates") or {}
    if d.get("local_paths_exposed"):
        errors.append("local_paths_exposed=true")
    if status in TERMINAL:
        if d.get("required_acks_present") is not True: errors.append("terminal delivery status without required_acks_present=true")
        required_ids = set(d.get("required_outbox_events") or [])
        acked_ids = {e.get("event_id") for e in d.get("outbox_events", []) if e.get("ack_status") in ["sent", "duplicate"]}
        missing = required_ids - acked_ids
        if missing: errors.append("terminal delivery missing acked events: " + ", ".join(sorted(missing)))
        required_attachments = [a for a in d.get("attachments", []) if a.get("required")]
        if len(required_attachments) < 2: errors.append("terminal delivery missing required attachments")
        for a in required_attachments:
            if a.get("sent") is not True: errors.append(f"required attachment not provider-acknowledged: {a.get('event_id')}")
    provider_gate = (gates.get("provider_ack_gate") or {}).get("status")
    external_gate = (gates.get("external_delivery_gate") or {}).get("status")
    final_gate = (gates.get("final_user_claim_gate") or {}).get("status")
    if status == "stub_delivered":
        if d.get("stub_delivery") is not True: errors.append("stub_delivered without stub_delivery=true")
        if d.get("real_external_delivery") is not False: errors.append("stub_delivered with real_external_delivery!=false")
        if d.get("delivery_claim_allowed") is not False: errors.append("stub_delivered must not allow external delivery claim")
        if provider_gate != "pass": errors.append("stub_delivered provider_ack_gate must pass")
        if external_gate != "stub_only": errors.append("stub_delivered external_delivery_gate must be stub_only")
        if final_gate != "stub_only": errors.append("stub_delivered final_user_claim_gate must be stub_only")
    if status == "delivered":
        if d.get("delivery_claim_allowed") is not True: errors.append("delivered without delivery_claim_allowed=true")
        if d.get("real_external_delivery") is not True: errors.append("delivered without real_external_delivery=true")
        if provider_gate != "pass" or external_gate != "pass" or final_gate != "pass": errors.append("delivered requires provider/external/final gates pass")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: delivery manifest validates v17.2 proof semantics"); return 0
if __name__ == "__main__": raise SystemExit(main())
