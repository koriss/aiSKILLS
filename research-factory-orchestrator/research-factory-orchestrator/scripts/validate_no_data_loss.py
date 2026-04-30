#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_evidence_vault")
    args = ap.parse_args()
    data = json.loads(Path(args.raw_evidence_vault).read_text(encoding="utf-8"))
    errors = []
    for section in ["sources","extracted_nodes","raw_claims","rejected","provenance"]:
        if section not in data:
            errors.append(f"missing vault section: {section}")
    for n in data.get("extracted_nodes", []):
        if n.get("collected") and n.get("stored_in_package") is False:
            errors.append(f"{n.get('node_id','?')}: collected but not stored")
        if n.get("shown_in_telegram") and n.get("sensitivity") in ["personal_public","private_or_sensitive","unknown"]:
            errors.append(f"{n.get('node_id','?')}: sensitive node shown in Telegram")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no-data-loss vault validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
