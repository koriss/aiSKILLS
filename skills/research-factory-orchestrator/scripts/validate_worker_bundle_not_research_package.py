#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package_zip")
    args = ap.parse_args()
    with zipfile.ZipFile(args.package_zip) as z:
        names = set(z.namelist())
    has_worker_dirs = any(n.startswith("SA-") or "/SA-" in n for n in names)
    has_runtime = {"run.json","entrypoint-proof.json","runtime-status.json","delivery-manifest.json"}.issubset(names)
    if has_worker_dirs and not has_runtime:
        print("worker bundle is not a research package", file=sys.stderr)
        return 1
    print("OK: package is not worker-bundle-only")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
