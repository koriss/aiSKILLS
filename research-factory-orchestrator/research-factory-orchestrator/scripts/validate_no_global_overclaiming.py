#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys, re

PATTERNS = [
    r"все\s+факты\s+верифицированы",
    r"все\s+факты\s+подтверждены",
    r"все\s+ключевые\s+факты",
    r"all\s+facts\s+verified",
    r"all\s+key\s+facts",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--claims", required=True)
    args = ap.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8")).get("claims", [])
    has_global = any(re.search(p, text, re.I) for p in PATTERNS)
    errors = []
    if has_global:
        bad = [c for c in claims if c.get("verification_status") not in ["confirmed"]]
        if bad:
            errors.append(f"global overclaiming: {len(bad)} non-confirmed claims exist")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no unsupported global overclaiming")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
