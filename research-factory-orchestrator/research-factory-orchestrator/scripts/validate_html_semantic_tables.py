#!/usr/bin/env python3
from pathlib import Path
import argparse, sys, re

REQUIRED_HEADERS = [
    "claim_id",
    "source_id",
    "verification_status",
    "citation_anchor",
    "stage",
    "artifact",
    "validator",
    "sha256",
]

PERSON_HEADERS = [
    "identity_status",
    "hard_signals",
    "used_in_report",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--person", action="store_true")
    args = ap.parse_args()

    txt = Path(args.html).read_text(encoding="utf-8", errors="replace").lower()
    errors = []
    for h in REQUIRED_HEADERS:
        if h.lower() not in txt:
            errors.append(f"missing semantic table header: {h}")
    if args.person:
        for h in PERSON_HEADERS:
            if h.lower() not in txt:
                errors.append(f"missing person identity table header: {h}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: HTML semantic tables validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
