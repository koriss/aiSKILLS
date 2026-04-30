#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("claim_citation_map")
    ap.add_argument("--claims", required=True)
    args = ap.parse_args()

    cmap = json.loads(Path(args.claim_citation_map).read_text(encoding="utf-8"))
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
    mapped = {m.get("claim_id") for m in cmap.get("mappings", []) if m.get("claim_id")}
    errors = []

    if cmap.get("all_verified_claims_cited") is not True:
        errors.append("all_verified_claims_cited != true")

    for c in claims:
        if c.get("verification_status") == "confirmed" and c.get("claim_id") not in mapped:
            errors.append(f"confirmed claim missing from claim-citation-map: {c.get('claim_id')}")

    for m in cmap.get("mappings", []):
        if not m.get("inline_markers"):
            errors.append(f"mapping missing inline_markers: {m.get('claim_id')}")
        if not m.get("full_urls"):
            errors.append(f"mapping missing full_urls: {m.get('claim_id')}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: claim citation map validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
