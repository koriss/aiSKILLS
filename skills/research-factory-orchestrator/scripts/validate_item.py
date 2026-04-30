#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys, subprocess

REQUIRED = [
    "full-report.html",
    "html-report-delivery.json",
    "chat-summary.json",
    "sources.json",
    "source-quality.json",
    "source-snapshots.json",
    "evidence-cards.json",
    "evidence-map.json",
    "claims-registry.json",
    "fact-check.html",
    "citation-locator.html",
    "adversarial-review.json",
    "error-audit.json",
    "final-answer-gate.json",
    "validation-transcript.json",
    "research-package-zip-manifest.json",
    "claim-citation-map.json",
    "all-source-fusion-map.json",
    "source-provenance.json",
    "int-coverage-matrix.json",
    "global-merge-plan.json",
    "watchdog-state.json",
    "shard-ledger.json",
    "workplan.json",
    "wiki-references.json",
    "inline-citations.json",
    "unsearched-categories.json",
    "exhaustive-search-ledger.json",
    "coverage-matrix.json",
    "evidence-debt.json",
    "search-ledger.json",
    "research-package.json",
    "completion-proof.json"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("item_dir")
    args = ap.parse_args()
    item = Path(args.item_dir)
    errors = []
    if item.name == "_template":
        errors.append("_template cannot be a completed item")
    for rel in REQUIRED:
        p = item / rel
        if not p.exists() or p.stat().st_size == 0:
            errors.append(f"missing or empty: {rel}")
        elif rel.endswith(".json"):
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"bad json {rel}: {e}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: item has minimum completion package")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
