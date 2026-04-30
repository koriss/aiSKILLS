#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys, hashlib

def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()

    manifest = Path(args.manifest)
    root = Path(args.root) if args.root else manifest.parent
    data = json.loads(manifest.read_text(encoding="utf-8"))
    errors = []
    for art in data.get("artifacts", []):
        rel = art.get("path")
        if not rel:
            errors.append("artifact missing path")
            continue
        p = root / rel
        if not p.exists():
            errors.append(f"artifact path missing: {rel}")
        if art.get("sha256") and p.exists() and sha256(p) != art.get("sha256"):
            errors.append(f"sha256 mismatch: {rel}")
        if art.get("role") in ["final", "full_html_report"] and "draft" in str(rel).lower():
            errors.append(f"final artifact points to draft path: {rel}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: artifact manifest validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
