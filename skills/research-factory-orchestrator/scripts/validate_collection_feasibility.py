#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

VALID = {"direct_available","public_derivative_only","user_provided_only","not_applicable","not_available_to_agent"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection_feasibility")
    args = ap.parse_args()
    data = json.loads(Path(args.collection_feasibility).read_text(encoding="utf-8"))
    errors = []
    for f in data.get("families", []):
        status = f.get("direct_collection_status")
        if status not in VALID:
            errors.append(f"bad direct_collection_status: {f.get('int_family')}={status}")
        if status != "direct_available" and not f.get("allowed_claim_style"):
            errors.append(f"{f.get('int_family')}: missing allowed_claim_style")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: collection feasibility validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
