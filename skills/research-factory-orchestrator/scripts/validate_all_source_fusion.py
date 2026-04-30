#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("all_source_fusion_map")
    args = ap.parse_args()
    data = json.loads(Path(args.all_source_fusion_map).read_text(encoding="utf-8"))
    errors = []
    for c in data.get("claims", []):
        if c.get("all_source_assessment") is True:
            families = set(c.get("supporting_int_families", []))
            if len(families) < 2:
                errors.append(f"all-source claim with <2 INT/source families: {c.get('claim_id')}")
            if c.get("independent_origin_count", 0) < 2:
                errors.append(f"all-source claim with <2 independent origins: {c.get('claim_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: all-source fusion validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
