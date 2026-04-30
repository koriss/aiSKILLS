#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("identity_candidates")
    args = ap.parse_args()
    data = json.loads(Path(args.identity_candidates).read_text(encoding="utf-8"))
    candidates = data.get("candidates", data if isinstance(data, list) else [])
    errors = []
    for c in candidates:
        if c.get("identity_status") in ["confirmed", "probable"] and c.get("critical_conflicts"):
            errors.append(f"confirmed/probable identity has critical conflicts: {c.get('candidate_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: identity conflicts validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
