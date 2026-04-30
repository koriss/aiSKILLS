#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED_GATES = [
    "runtime_gate", "package_gate", "content_gate", "provider_ack_gate", "external_delivery_gate", "final_user_claim_gate"
]

def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); args = ap.parse_args()
    root = Path(args.run_dir); errors=[]
    manifest_path = root/"delivery-manifest.json"; final_path = root/"final-answer-gate.json"
    if not manifest_path.exists(): errors.append("missing delivery-manifest.json")
    if not final_path.exists(): errors.append("missing final-answer-gate.json")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    manifest = load(manifest_path); final = load(final_path)
    gates = manifest.get("gates") or {}
    final_gates = final.get("gates") or {}
    for g in REQUIRED_GATES:
        if g not in gates: errors.append(f"manifest missing gate {g}")
        if g not in final_gates: errors.append(f"final-answer-gate missing gate {g}")
        if g in gates and "status" not in gates[g]: errors.append(f"manifest gate {g} missing status")
        if g in gates and "passed" not in gates[g]: errors.append(f"manifest gate {g} missing passed")
    status = manifest.get("delivery_status")
    provider = (gates.get("provider_ack_gate") or {}).get("status")
    external = (gates.get("external_delivery_gate") or {}).get("status")
    final_claim = (gates.get("final_user_claim_gate") or {}).get("status")
    if manifest.get("required_acks_present") and provider != "pass": errors.append("required_acks_present=true but provider_ack_gate is not pass")
    if status == "stub_delivered":
        if provider != "pass": errors.append("stub delivered requires provider_ack_gate=pass")
        if external != "stub_only": errors.append("stub delivered requires external_delivery_gate=stub_only")
        if final_claim != "stub_only": errors.append("stub delivered requires final_user_claim_gate=stub_only")
        if manifest.get("delivery_claim_allowed") is not False: errors.append("stub delivered cannot allow external delivery claim")
        if final.get("passed") is not False: errors.append("stub delivered cannot set final-answer-gate.passed=true")
    if status == "delivered":
        if provider != "pass" or external != "pass" or final_claim != "pass": errors.append("real delivered requires provider/external/final gates pass")
        if manifest.get("delivery_claim_allowed") is not True: errors.append("real delivered requires delivery_claim_allowed=true")
        if final.get("passed") is not True: errors.append("real delivered requires final-answer-gate.passed=true")
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: v17.2 gate semantics validate"); return 0
if __name__ == "__main__": raise SystemExit(main())
