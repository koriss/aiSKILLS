#!/usr/bin/env python3
"""Validate the current v19 runtime skeleton produced by scripts/init_runtime.py."""
from pathlib import Path
import argparse, json, sys

CURRENT_REQUIRED = [
    "run.json", "run-state.json", "task-profile.json", "coverage-matrix.json",
    "work-unit-plan.json", "subagent-plan.json", "subagent-ledger.json",
    "collection-coverage-contract.json", "collection-coverage-result.json",
    "ledgers/search-ledger.json", "ledgers/tool-call-ledger.json", "ledgers/progress-ledger.json", "ledgers/retry-ledger.json",
    "claims/claims-registry.json", "evidence/evidence-cards.json", "graph/target-graph.json",
    "raw-evidence/raw-evidence-vault.json", "provenance-manifest.json", "artifact-manifest.json",
    "validation-transcript.json", "delivery-manifest.json", "attachment-ledger.json", "final-answer-gate.json",
    "report/semantic-report.json", "report/full-report.md", "report/full-report.html", "chat/chat-message-plan.json",
    "interface/interface-request.json", "interface/normalized-command.json", "jobs/runtime-job.json", "outbox/outbox-policy.json",
]
CURRENT_REQUIRED_DIRS = ["work-units", "subagents", "ledgers", "claims", "evidence", "raw-evidence", "report", "chat", "outbox", "delivery-acks", "provider-payloads"]

def check_json(path: Path, errors):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append({"path": str(path), "error": f"invalid_json: {e}"})

def validate_current(root: Path):
    errors=[]
    for rel in CURRENT_REQUIRED_DIRS:
        p=root/rel
        if not p.exists() or not p.is_dir():
            errors.append({"path": rel, "error": "missing_directory"})
    for rel in CURRENT_REQUIRED:
        p=root/rel
        if not p.exists() or p.stat().st_size == 0:
            errors.append({"path": rel, "error": "missing_or_empty"})
        elif rel.endswith(".json"):
            check_json(p, errors)
    # semantic sanity checks matching init_runtime.py
    for rel, key in [("run.json", "run_id"), ("work-unit-plan.json", "work_units"), ("subagent-plan.json", "assignments")]:
        p=root/rel
        if p.exists() and p.stat().st_size:
            try:
                data=json.loads(p.read_text(encoding="utf-8"))
                if key not in data:
                    errors.append({"path": rel, "error": f"missing_key:{key}"})
            except Exception:
                pass
    return errors

def main():
    ap=argparse.ArgumentParser(description="Validate RFO runtime artifacts.")
    ap.add_argument("project_dir")
    args=ap.parse_args()
    root=Path(args.project_dir)
    errors = validate_current(root)
    result={"status":"pass" if not errors else "fail", "profile":"current", "project_dir":str(root), "errors":errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
