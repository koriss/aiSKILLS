#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED = ["source_id","source_family","int_family","collection_form","provenance","supports_claim_ids"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_provenance")
    args = ap.parse_args()
    data = json.loads(Path(args.source_provenance).read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    errors = []
    if not sources:
        errors.append("source provenance sources empty")
    for s in sources:
        for k in REQUIRED:
            if k not in s or s.get(k) in [None, ""]:
                errors.append(f"{s.get('source_id')}: missing {k}")
        if s.get("direct_collection") is True and not s.get("direct_collection_evidence"):
            errors.append(f"{s.get('source_id')}: direct_collection=true without evidence")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: source provenance validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
