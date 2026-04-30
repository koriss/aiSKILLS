#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED_SECTIONS = [
    "executive-summary",
    "scope-method",
    "key-facts",
    "structured-data",
    "contradictions-gaps",
    "references"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    args = ap.parse_args()
    data = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
    errors = []

    if not data.get("summary", {}).get("verdict"):
        errors.append("summary.verdict missing")
    if not data.get("summary", {}).get("key_findings"):
        errors.append("summary.key_findings missing")
    sections = {s.get("section_id") for s in data.get("sections", [])}
    for req in REQUIRED_SECTIONS:
        if req not in sections:
            errors.append(f"missing required section: {req}")
    if not data.get("sources"):
        errors.append("sources empty")
    if not data.get("claims"):
        errors.append("claims empty")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: report structure validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
