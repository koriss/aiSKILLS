#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re

CLAIMS = re.compile(r"Research Factory Orchestrator|full pipeline|runtime_version|runtime-status-json|entrypoint-proof-json|v17\.|v18\.", re.I)

def read_texts(path):
    p=Path(path)
    if p.is_dir():
        paths=list((p/"report").glob("*.html"))+list((p/"chat").glob("*.txt"))
        return "\n".join(x.read_text(encoding="utf-8", errors="replace") for x in paths if x.exists()), p
    return p.read_text(encoding="utf-8", errors="replace"), None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); args=ap.parse_args()
    text, run_dir = read_texts(args.path)
    errors=[]
    if CLAIMS.search(text):
        if run_dir is None:
            errors.append("runtime/RFO claim appears outside a run-dir with entrypoint proof")
        else:
            required=["entrypoint-proof.json","runtime-status.json","jobs/runtime-job.json","observability-events.jsonl"]
            missing=[r for r in required if not (run_dir/r).exists()]
            if missing:
                errors.append("runtime/RFO claim requires missing artifacts: "+", ".join(missing))
            else:
                try:
                    ep=json.loads((run_dir/"entrypoint-proof.json").read_text(encoding="utf-8"))
                    if ep.get("entrypoint")!="scripts/run_research_factory.py" or ep.get("invocation_mode")!="runtime":
                        errors.append("entrypoint proof is not valid runtime invocation")
                except Exception as e:
                    errors.append(f"entrypoint-proof invalid JSON: {e}")
    print(json.dumps({"status":"pass" if not errors else "fail","errors":errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
