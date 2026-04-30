#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); args = ap.parse_args()
    root = Path(args.run_dir); events = sorted((root/"outbox").glob("OUT-*.json")); errors = []
    if not events: errors.append("no outbox events")
    for evp in events:
        ev = json.loads(evp.read_text(encoding="utf-8"))
        eid = ev.get("event_id")
        if ev.get("status") != "sent": errors.append(f"{eid}: not sent")
        ackp = root/"delivery-acks"/f"{eid}.json"
        if not ackp.exists(): errors.append(f"{eid}: missing delivery ack"); continue
        ack = json.loads(ackp.read_text(encoding="utf-8"))
        for key in ["stub_delivery", "real_external_delivery", "provider_payload_path"]:
            if key not in ack: errors.append(f"{eid}: ack missing {key}")
        if ack.get("idempotency_key") != ev.get("idempotency_key"): errors.append(f"{eid}: idempotency key mismatch")
        if ack.get("provider") != ev.get("provider"): errors.append(f"{eid}: provider mismatch")
    manifest = root/"delivery-manifest.json"; gate = root/"final-answer-gate.json"
    if not manifest.exists(): errors.append("missing delivery-manifest.json")
    else:
        m = json.loads(manifest.read_text(encoding="utf-8"))
        if m.get("delivery_status") not in ["delivered", "stub_delivered"]: errors.append(f"delivery-manifest not terminal: {m.get('delivery_status')}")
        g = m.get("gates") or {}
        if (g.get("provider_ack_gate") or {}).get("status") != "pass": errors.append("provider_ack_gate not pass")
        if m.get("delivery_status") == "stub_delivered":
            if (g.get("external_delivery_gate") or {}).get("status") != "stub_only": errors.append("stub external_delivery_gate not stub_only")
            if m.get("delivery_claim_allowed") is not False: errors.append("stub delivery overclaims delivery_claim_allowed")
        if m.get("delivery_status") == "delivered":
            if (g.get("external_delivery_gate") or {}).get("status") != "pass": errors.append("real external_delivery_gate not pass")
            if m.get("delivery_claim_allowed") is not True: errors.append("real delivery claim not allowed")
    if not gate.exists(): errors.append("missing final-answer-gate.json")
    else:
        fg = json.loads(gate.read_text(encoding="utf-8"))
        if fg.get("delivery_status") == "stub_delivered" and fg.get("passed") is not False: errors.append("stub final-answer-gate passed=true overclaim")
        if fg.get("delivery_status") == "delivered" and fg.get("passed") is not True: errors.append("real final-answer-gate not passed")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: outbox delivery validates v17.2 proof semantics"); return 0
if __name__ == "__main__": raise SystemExit(main())
