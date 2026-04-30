#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile, sys

BASE_REQUIRED = [
    "full-report.html",
    "chat-summary.json",
    "completion-proof.json",
    "validation-transcript.json",
    "research-package.json",
    "search-ledger.json",
    "evidence-debt.json",
    "sources.json",
    "source-quality.json",
    "source-snapshots.json",
    "evidence-cards.json",
    "claims-registry.json",
    "citation-locator.json",
    "adversarial-review.json",
    "error-audit.json",
    "final-answer-gate.json",
    "coverage-matrix.json",
    "exhaustive-search-ledger.json",
    "unsearched-categories.json",
    "inline-citations.json",
    "wiki-references.json",
    "claim-citation-map.json",
]
PERSON_REQUIRED = [
    "identity-candidates.json",
    "identity-resolution.json",
    "identity-confusion-set.json",
    "identity-graph.json",
    "person-data-classification.json",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path")
    ap.add_argument("--person", action="store_true")
    args = ap.parse_args()

    errors = []
    with zipfile.ZipFile(args.zip_path) as z:
        names = z.namelist()
        normalized = {Path(n).name for n in names}
        required = BASE_REQUIRED + (PERSON_REQUIRED if args.person else [])
        for r in required:
            if r not in normalized:
                errors.append(f"missing required file in package: {r}")
        if not any("stage-records/" in n for n in names):
            errors.append("missing stage-records/")
        for n in names:
            if n.startswith("/") or ".." in Path(n).parts:
                errors.append(f"unsafe path: {n}")
        for info in z.infolist():
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                errors.append(f"symlink entry: {info.filename}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: research-package.zip validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
