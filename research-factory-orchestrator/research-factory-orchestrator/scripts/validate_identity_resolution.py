#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("identity_resolution")
    args = ap.parse_args()

    data = json.loads(Path(args.identity_resolution).read_text(encoding="utf-8"))
    errors = []
    for bucket in ["confirmed_profiles", "probable_profiles"]:
        for p in data.get(bucket, []):
            if not p.get("hard_signals"):
                errors.append(f"{bucket} profile without hard_signals: {p.get('candidate_id') or p.get('url')}")
            if p.get("critical_conflicts"):
                errors.append(f"{bucket} profile has critical conflicts: {p.get('candidate_id') or p.get('url')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: identity resolution validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
