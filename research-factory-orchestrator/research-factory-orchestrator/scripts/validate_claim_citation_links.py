#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True)
    ap.add_argument("--citations", required=True)
    args = ap.parse_args()
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
    citations = json.loads(Path(args.citations).read_text(encoding="utf-8")).get("citations", [])
    cited = {c.get("claim_id") for c in citations if c.get("claim_id")}
    errors = []
    for c in claims:
        if c.get("verification_status") == "confirmed" and c.get("claim_id") not in cited:
            errors.append(f"confirmed claim without citation: {c.get('claim_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: confirmed claims have citation links")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
