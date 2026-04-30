#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED = ["sources","source_quality","evidence_cards","claims","completion_proof"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("research_package")
    args = ap.parse_args()
    data = json.loads(Path(args.research_package).read_text(encoding="utf-8"))
    errors = []
    for k in REQUIRED:
        if k not in data:
            errors.append(f"missing {k}")
    if not data.get("sources"):
        errors.append("sources empty")
    if not data.get("claims"):
        errors.append("claims empty")
    if not data.get("completion_proof"):
        errors.append("completion_proof empty")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: research package validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
