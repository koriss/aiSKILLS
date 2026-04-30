#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources-json", required=True)
    ap.add_argument("--html")
    ap.add_argument("--declared", type=int)
    args = ap.parse_args()
    data = json.loads(Path(args.sources_json).read_text(encoding="utf-8"))
    sources = data.get("sources", data if isinstance(data, list) else [])
    actual = len(sources)
    errors = []
    if args.declared is not None and args.declared != actual:
        errors.append(f"declared source count {args.declared} != sources.json count {actual}")
    if args.html:
        text = Path(args.html).read_text(encoding="utf-8", errors="ignore")
        refs = len(set(re.findall(r'id=[\"\\\']ref-\\d+[\"\\\']', text)))
        if refs and refs != actual:
            errors.append(f"html refs {refs} != sources.json count {actual}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: source count consistency validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
