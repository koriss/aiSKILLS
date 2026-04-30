#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    args = ap.parse_args()
    root = Path(args.project_dir)
    script = Path(__file__).with_name("validate_item.py")
    items = [p for p in (root / "items").iterdir() if p.is_dir() and p.name != "_template"] if (root / "items").exists() else []
    if not items:
        print("no real items found", file=sys.stderr)
        return 1
    failed = []
    for item in items:
        res = subprocess.run([sys.executable, str(script), str(item)], capture_output=True, text=True)
        if res.returncode != 0:
            failed.append(f"{item}:\n{res.stderr}")
    if failed:
        print("\n".join(failed), file=sys.stderr)
        return 1
    print(f"OK: {len(items)} item(s) validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
