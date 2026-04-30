#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); args = ap.parse_args()
    root=Path(args.run_dir); errors=[]
    manifest=read(root/"delivery-manifest.json")
    final=read(root/"final-answer-gate.json")
    if manifest.get("stub_delivery") is True or manifest.get("delivery_status") == "stub_delivered":
        if manifest.get("real_external_delivery") is not False: errors.append("stub manifest claims real_external_delivery")
        if manifest.get("external_delivery_claim_allowed") is not False: errors.append("stub manifest allows external_delivery_claim")
        if manifest.get("delivery_claim_allowed") is not False: errors.append("stub manifest allows delivery_claim_allowed")
        gates=manifest.get("gates") or {}
        if (gates.get("external_delivery_gate") or {}).get("status") != "stub_only": errors.append("stub external_delivery_gate is not stub_only")
        if (gates.get("final_user_claim_gate") or {}).get("status") != "stub_only": errors.append("stub final_user_claim_gate is not stub_only")
        if final.get("passed") is not False: errors.append("stub final-answer-gate passed=true")
        if final.get("external_delivery_gate") != "stub_only": errors.append("stub final external_delivery_gate not stub_only")
        if final.get("final_user_claim_gate") != "stub_only": errors.append("stub final user claim gate not stub_only")
    for ackp in sorted((root/"delivery-acks").glob("OUT-*.json")):
        ack=read(ackp)
        if ack.get("stub_delivery") is True and ack.get("real_external_delivery") is True:
            errors.append(f"{ackp.name}: ack both stub and real")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: stub delivery is not treated as external delivery"); return 0
if __name__ == "__main__": raise SystemExit(main())
