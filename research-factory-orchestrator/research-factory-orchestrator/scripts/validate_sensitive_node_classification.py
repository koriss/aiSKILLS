#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

ALLOWED = {"public_official","public_professional","public_organization","public_registry","public_event","personal_public","private_or_sensitive","leaked_or_untrusted","unknown"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nodes_json")
    args = ap.parse_args()
    data = json.loads(Path(args.nodes_json).read_text(encoding="utf-8"))
    nodes = data.get("nodes") or data.get("extracted_nodes") or data.get("sensitive_nodes") or (data if isinstance(data, list) else [])
    errors = []
    for n in nodes:
        if n.get("sensitivity") not in ALLOWED:
            errors.append(f"{n.get('node_id','?')}: invalid/missing sensitivity")
        if not n.get("display_policy"):
            errors.append(f"{n.get('node_id','?')}: missing display_policy")
        if not (n.get("source_ids") or n.get("source_id")):
            errors.append(f"{n.get('node_id','?')}: missing source")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: sensitive node classification validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
