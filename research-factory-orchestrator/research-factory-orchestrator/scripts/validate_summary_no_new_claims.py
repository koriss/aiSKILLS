#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def collect_claim_ids(claims_registry):
    claims = json.loads(Path(claims_registry).read_text(encoding="utf-8")).get("claims", [])
    return {c.get("claim_id") for c in claims if c.get("claim_id")}

def iter_claim_refs(items):
    for it in items or []:
        if isinstance(it, dict):
            for cid in it.get("claim_ids", []) or []:
                yield cid
        elif isinstance(it, str):
            # Free-form strings are allowed only for known gaps/uncertainty, not verified factual findings.
            continue

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--claims", required=True)
    args = ap.parse_args()

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    valid_ids = collect_claim_ids(args.claims)
    errors = []

    if not summary.get("html_report_path"):
        errors.append("chat summary missing html_report_path")

    for section in ["key_findings", "verified_claims"]:
        for cid in iter_claim_refs(summary.get(section, [])):
            if cid not in valid_ids:
                errors.append(f"{section} references unknown claim_id: {cid}")

    # Require structured findings to include claim_ids unless section is empty.
    for section in ["key_findings", "verified_claims"]:
        for i, it in enumerate(summary.get(section, [])):
            if isinstance(it, dict) and not it.get("claim_ids"):
                errors.append(f"{section}[{i}] missing claim_ids")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: summary references known claims and HTML report")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
