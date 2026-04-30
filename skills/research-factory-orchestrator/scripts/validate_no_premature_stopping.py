#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", required=True)
    ap.add_argument("--search-ledger", required=True)
    args = ap.parse_args()

    coverage = json.loads(Path(args.coverage).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.search_ledger).read_text(encoding="utf-8"))
    errors = []

    if coverage.get("complete") is not True:
        errors.append("coverage incomplete")
    if ledger.get("unsearched_categories"):
        errors.append("search ledger contains unsearched categories")
    for c in coverage.get("categories", []):
        if c.get("status") in [None, "", "ignored"]:
            errors.append(f"category appears ignored: {c.get('category')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no premature stopping detected")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
