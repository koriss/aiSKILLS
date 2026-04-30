#!/usr/bin/env python3
from pathlib import Path
import argparse, json, zipfile, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package_zip")
    ap.add_argument("--skill-dir", required=True)
    args = ap.parse_args()
    contract = json.loads((Path(args.skill_dir) / "contracts" / "canonical-package-layout-contract.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(args.package_zip) as z:
        names = set(z.namelist())
    errors = []
    for rel in contract.get("required_paths", []):
        if rel not in names:
            errors.append(f"missing package path: {rel}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: canonical package layout validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
