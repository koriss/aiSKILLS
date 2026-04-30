#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

VALID = {"found","searched_not_found","blocked_with_reason","not_applicable_with_reason","public_derivative_only","user_provided_only","not_available_to_agent","searched_low_yield"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("int_coverage_matrix")
    args = ap.parse_args()
    data = json.loads(Path(args.int_coverage_matrix).read_text(encoding="utf-8"))
    errors = []
    fams = data.get("int_families", [])
    if not fams:
        errors.append("int_families empty")
    for f in fams:
        st = f.get("status")
        if st not in VALID:
            errors.append(f"invalid INT family status: {f.get('int_family')}={st}")
        if st in ["blocked_with_reason","not_applicable_with_reason","public_derivative_only","user_provided_only","not_available_to_agent"] and not f.get("reason"):
            errors.append(f"{f.get('int_family')}: status {st} missing reason")
    if data.get("single_int_lockin") is True:
        errors.append("single_int_lockin=true")
    if data.get("all_source_claimed") and not data.get("all_source_supported"):
        errors.append("all_source_claimed but all_source_supported=false")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: INT coverage matrix validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
