#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

VALID = {"searched","found","searched_not_found","blocked_with_reason","not_applicable_with_reason"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("coverage_matrix")
    args = ap.parse_args()
    data = json.loads(Path(args.coverage_matrix).read_text(encoding="utf-8"))
    errors = []
    if data.get("complete") is not True:
        errors.append("coverage matrix complete != true")
    categories = data.get("categories", [])
    if not categories:
        errors.append("coverage categories empty")
    for c in categories:
        status = c.get("status")
        if status not in VALID:
            errors.append(f"invalid coverage status for {c.get('category')}: {status}")
        if status in ["blocked_with_reason","not_applicable_with_reason"] and not c.get("reason"):
            errors.append(f"{status} missing reason: {c.get('category')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: coverage matrix validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
