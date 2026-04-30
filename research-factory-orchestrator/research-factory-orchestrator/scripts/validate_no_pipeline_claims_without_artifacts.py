#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys, re

CLAIM_PATTERNS = {
    "sources": [r"sources? collected", r"источников собрано", r"sources:\s*\d+"],
    "evidence_cards": [r"evidence cards?", r"карточ"],
    "final_answer_gate": [r"final-answer gate", r"gates?\s+pass", r"gate.*pass"],
    "adversarial_review": [r"adversarial review", r"критическ"],
    "citation_locator": [r"citation anchors?", r"citation locator", r"якор"],
    "stage_records": [r"stages? completed", r"strict-full", r"pipeline"]
}

REQUIRED_ARTIFACT_KEYWORDS = {
    "sources": "sources.json",
    "evidence_cards": "evidence-cards.json",
    "final_answer_gate": "final-answer-gate.json",
    "adversarial_review": "adversarial-review.json",
    "citation_locator": "citation-locator",
    "stage_records": "stage-record"
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--completion-proof", required=True)
    args = ap.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
    proof = json.loads(Path(args.completion_proof).read_text(encoding="utf-8"))
    artifact_paths = " ".join(str(a.get("path","")) for a in proof.get("artifacts", []))
    errors = []

    for key, patterns in CLAIM_PATTERNS.items():
        claimed = any(re.search(p, text, re.I) for p in patterns)
        if claimed and REQUIRED_ARTIFACT_KEYWORDS[key] not in artifact_paths:
            errors.append(f"pipeline claim '{key}' without matching artifact proof")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: pipeline claims have artifact proof")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
