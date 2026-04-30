#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("person_data_classification")
    args = ap.parse_args()
    data = json.loads(Path(args.person_data_classification).read_text(encoding="utf-8"))
    errors = []
    for r in data.get("records", []):
        for k in ["public_source","identity_confirmed","relevance","sensitivity_category","verification_status","confidence","final_report_section"]:
            if k not in r:
                errors.append(f"record missing {k}: {r.get('field') or r.get('claim_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: person data classification validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
