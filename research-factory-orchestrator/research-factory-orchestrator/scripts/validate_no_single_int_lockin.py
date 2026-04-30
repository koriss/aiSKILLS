#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("int_coverage_matrix")
    args = ap.parse_args()
    data = json.loads(Path(args.int_coverage_matrix).read_text(encoding="utf-8"))
    found = [f for f in data.get("int_families", []) if f.get("status") == "found"]
    applicable_not_found = [f for f in data.get("int_families", []) if f.get("status") in ["searched_not_found","searched_low_yield"]]
    errors = []
    if len(found) < 2 and not applicable_not_found:
        errors.append("less than 2 found INT/source families and no searched_not_found coverage")
    if data.get("single_int_lockin") is True:
        errors.append("single_int_lockin=true")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no single INT lock-in")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
