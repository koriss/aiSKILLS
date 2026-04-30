#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED = [
    "work_unit_compilation_validated",
    "no_single_work_unit_run",
    "no_single_subagent_run",
    "subagent_quorum_met",
    "collection_coverage_met",
    "search_ledger_present",
    "subagent_ledger_present",
    "artifact_manifest_validated",
    "provenance_manifest_validated",
    "standalone_html_validated",
    "telegram_no_tables",
    "telegram_no_local_paths",
    "no_sensitive_data_in_telegram",
    "research_package_zip_created",
    "research_package_zip_sent",
    "html_report_sent",
    "delivery_manifest_validated",
    "failure_corpus_evals_passed",
    "no_manual_check_as_final_proof"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gate_json")
    args = ap.parse_args()
    data = json.loads(Path(args.gate_json).read_text(encoding="utf-8"))
    errors = []
    if data.get("passed") is not True:
        errors.append("final-answer gate passed != true")
    checks = data.get("checks", {})
    for k in REQUIRED:
        if checks.get(k) is not True:
            errors.append(f"critical check not true: {k}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: final-answer gate validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
