#!/usr/bin/env python3
from pathlib import Path
import argparse, json, shutil, sys, tempfile
from datetime import datetime, timezone

REQUIRED = ["OUT-0001", "OUT-0002", "OUT-0003"]

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def write(p,obj):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def make_run(root, provider="telegram", ack_mode="stub", missing=None, failed=None):
    name = ack_mode + ("_missing_" + missing if missing else "") + ("_failed_" + failed if failed else "")
    r=Path(root)/"runs"/name
    if r.exists(): shutil.rmtree(r)
    r.mkdir(parents=True, exist_ok=True)
    write(r/"run.json", {"run_id":"RUN-NEG", "job_id":"JOB-NEG", "command_id":"CMD-NEG"})
    write(r/"entrypoint-proof.json", {"run_id":"RUN-NEG"})
    write(r/"runtime-status.json", {"run_id":"RUN-NEG", "state":"delivery_ready"})
    (r/"package").mkdir(exist_ok=True); (r/"package"/"research-package.zip").write_bytes(b"PK\x05\x06"+b"\0"*18)
    (r/"report").mkdir(exist_ok=True); (r/"report"/"full-report.html").write_text("<html>ok</html>", encoding="utf-8")
    (r/"chat").mkdir(exist_ok=True); (r/"chat"/"message-001.txt").write_text("ok", encoding="utf-8")
    write(r/"outbox"/"outbox-policy.json", {"required_events": REQUIRED})
    for eid in REQUIRED:
        typ = "send_message" if eid == "OUT-0001" else "send_file"
        payload = "chat/message-001.txt" if eid == "OUT-0001" else ("report/full-report.html" if eid == "OUT-0002" else "package/research-package.zip")
        write(r/"outbox"/f"{eid}.json", {"event_id":eid,"run_id":"RUN-NEG","job_id":"JOB-NEG","command_id":"CMD-NEG","provider":provider,"type":typ,"payload_path":payload,"payload_kind":"chat_message" if typ=="send_message" else "attachment","file_kind":None if typ=="send_message" else ("html_report" if eid=="OUT-0002" else "research_package"),"status":"sent","idempotency_key":"NEG:"+eid})
        if missing == eid: continue
        stub = ack_mode == "stub"
        real = ack_mode == "real"
        status = "failed" if failed == eid else "sent"
        write(r/"delivery-acks"/f"{eid}.json", {"ack_id":"ACK-"+eid,"event_id":eid,"run_id":"RUN-NEG","job_id":"JOB-NEG","command_id":"CMD-NEG","provider":provider,"status":status,"provider_message_id":("stub:" if stub else "real:")+eid,"idempotency_key":"NEG:"+eid,"provider_payload_path":"provider-payloads/x/"+eid+".json","stub_delivery":stub,"real_external_delivery":real,"created_at":now()})
    write(r/"delivery-manifest.json", {})
    write(r/"attachment-ledger.json", {})
    write(r/"final-answer-gate.json", {})
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--skill-dir", default=None); args=ap.parse_args()
    skill=Path(args.skill_dir or Path(__file__).resolve().parent.parent)
    sys.path.insert(0, str(skill/"scripts"))
    import outbox_delivery_worker as odw
    base=Path(tempfile.mkdtemp(prefix="rfo-gate-negative-"))
    errors=[]
    try:
        stub=make_run(base, provider="telegram", ack_mode="stub")
        odw.recompute_delivery_state(stub)
        md=read(stub/"delivery-manifest.json"); fg=read(stub/"final-answer-gate.json")
        if md.get("delivery_status") != "stub_delivered": errors.append("stub case did not become stub_delivered")
        if md.get("delivery_claim_allowed") is not False: errors.append("stub case allowed delivery claim")
        if fg.get("passed") is not False: errors.append("stub case set final passed true")
        if fg.get("external_delivery_gate") != "stub_only": errors.append("stub case external gate not stub_only")
        real=make_run(base, provider="cli", ack_mode="real")
        odw.recompute_delivery_state(real)
        md=read(real/"delivery-manifest.json"); fg=read(real/"final-answer-gate.json")
        if md.get("delivery_status") != "delivered": errors.append("real case did not become delivered")
        if md.get("delivery_claim_allowed") is not True: errors.append("real case did not allow delivery claim")
        if fg.get("passed") is not True: errors.append("real case did not pass final gate")
        miss=make_run(base, provider="telegram", ack_mode="stub", missing="OUT-0002")
        odw.recompute_delivery_state(miss)
        if read(miss/"delivery-manifest.json").get("delivery_status") != "partial_delivery": errors.append("missing ACK case not partial_delivery")
        fail=make_run(base, provider="telegram", ack_mode="stub", failed="OUT-0003")
        odw.recompute_delivery_state(fail)
        if read(fail/"delivery-manifest.json").get("delivery_status") != "failed": errors.append("failed ACK case not failed")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print("OK: delivery gate negative cases validate")
    return 0
if __name__ == "__main__": raise SystemExit(main())
