#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_family_confidence")
    args = ap.parse_args()
    data = json.loads(Path(args.source_family_confidence).read_text(encoding="utf-8"))
    errors = []
    for c in data.get("claim_confidence", []):
        if c.get("confidence") == "high":
            if c.get("source_family_variety", 0) < 2 and c.get("primary_source_count", 0) < 1:
                errors.append(f"high confidence without family variety or primary source: {c.get('claim_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: source family confidence validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
