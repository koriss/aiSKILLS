#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED = [
    "broad topical queries",
    "exact entity/title queries",
    "primary-source queries",
    "source-specific queries",
    "contrary/criticism/contradiction queries",
    "recent/date-bounded queries",
    "terminology/synonym/translation queries",
    "evidence-gap queries"
]

def norm(s): return str(s).strip().lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("search_ledger")
    args = ap.parse_args()
    data = json.loads(Path(args.search_ledger).read_text(encoding="utf-8"))
    fams = data.get("query_families", [])
    names = {norm(f.get("family","")) for f in fams}
    errors = []
    for r in REQUIRED:
        if norm(r) not in names:
            errors.append(f"missing query family: {r}")
    for f in fams:
        queries = f.get("queries", [])
        blocked = f.get("blocked", False)
        if not queries and not blocked:
            errors.append(f"family has neither queries nor blocked=true: {f.get('family')}")
        if blocked and not f.get("blocked_reason"):
            errors.append(f"blocked family missing blocked_reason: {f.get('family')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: search ledger validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
