#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

PATTERNS = [r"ALL-INT", r"all-source", r"multi-INT", r"multi-intelligence"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--fusion-map", required=True)
    args = ap.parse_args()
    txt = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
    data = json.loads(Path(args.fusion_map).read_text(encoding="utf-8"))
    claims = data.get("claims", [])
    supported = any(c.get("all_source_assessment") is True and len(set(c.get("supporting_int_families", []))) >= 2 for c in claims)
    has_label = any(re.search(p, txt, re.I) for p in PATTERNS)
    if has_label and not supported:
        print("all-source/multi-INT label used without supporting fusion map", file=sys.stderr)
        return 1
    print("OK: no all-INT overclaiming")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
