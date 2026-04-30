#!/usr/bin/env python3
"""Validate the CURRENT v18 runtime skeleton produced by scripts/init_runtime.py.

This validator intentionally does not validate the legacy items/_template/* layout.
Use --legacy only when validating archived pre-v18 skeletons.
"""
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
    "report/semantic-report.json", "report/full-report.html", "chat/chat-message-plan.json",
    "interface/interface-request.json", "interface/normalized-command.json", "jobs/runtime-job.json", "outbox/outbox-policy.json",
]
CURRENT_REQUIRED_DIRS = ["work-units", "subagents", "ledgers", "claims", "evidence", "raw-evidence", "report", "chat", "outbox", "delivery-acks", "provider-payloads"]
LEGACY_REQUIRED = [
    "runtime-contract.json", "runtime-state.json", "queue.json", "artifact-manifest.json", "tool-registry.json",
    "tool-permissions.json", "stage-records.json", "task-ledger.md", "progress-ledger.md",
    "items/_template/search-strategy.md", "items/_template/sources.json", "items/_template/source-quality.json", "items/_template/source-snapshots.json", "items/_template/contradiction-matrix.json",
    "items/_template/evidence-cards.json", "items/_template/evidence-map.json", "items/_template/claims-registry.json",
    "items/_template/fact-check.html", "items/_template/citation-locator.html", "items/_template/adversarial-review.json",
    "items/_template/error-audit.json", "items/_template/final-answer-gate.json", "items/_template/chat-summary.json", "items/_template/html-report-delivery.json", "items/_template/full-report.html",
    "items/_template/final.html",
]

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

def validate_legacy(root: Path):
    errors=[]
    for rel in LEGACY_REQUIRED:
        p=root/rel
        if not p.exists() or p.stat().st_size == 0:
            errors.append({"path": rel, "error": "missing_or_empty_legacy"})
        elif rel.endswith(".json"):
            check_json(p, errors)
    return errors

def main():
    ap=argparse.ArgumentParser(description="Validate RFO runtime artifacts.")
    ap.add_argument("project_dir")
    ap.add_argument("--profile", choices=["current", "legacy"], default="current")
    args=ap.parse_args()
    root=Path(args.project_dir)
    errors = validate_current(root) if args.profile == "current" else validate_legacy(root)
    result={"status":"pass" if not errors else "fail", "profile":args.profile, "project_dir":str(root), "errors":errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
