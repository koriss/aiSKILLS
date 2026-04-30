#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("unsearched_categories")
    args = ap.parse_args()
    data = json.loads(Path(args.unsearched_categories).read_text(encoding="utf-8"))
    errors = []
    if data.get("open_unsearched_count", 0) != 0:
        errors.append(f"open_unsearched_count != 0: {data.get('open_unsearched_count')}")
    for c in data.get("categories", []):
        if c.get("status") == "open":
            errors.append(f"open unsearched category: {c.get('category')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no open unsearched categories")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
