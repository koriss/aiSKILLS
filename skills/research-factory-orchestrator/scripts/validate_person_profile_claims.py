#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True)
    ap.add_argument("--identity-candidates", required=True)
    args = ap.parse_args()

    claims = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
    raw = json.loads(Path(args.identity_candidates).read_text(encoding="utf-8"))
    candidates = raw.get("candidates", raw if isinstance(raw, list) else [])
    allowed_sources = {c.get("source_id") for c in candidates if c.get("identity_status") in ["confirmed", "probable"]}
    candidate_sources = {c.get("source_id") for c in candidates if c.get("identity_status") not in ["confirmed", "probable"]}

    errors = []
    for claim in claims:
        for sid in claim.get("source_ids", []):
            if sid in candidate_sources and sid not in allowed_sources:
                errors.append(f"claim uses unconfirmed profile source {sid}: {claim.get('claim_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: person profile claims validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
