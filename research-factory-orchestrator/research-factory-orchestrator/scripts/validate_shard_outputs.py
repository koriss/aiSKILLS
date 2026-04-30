#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--shard-dir", required=True)
    args = ap.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    shard = Path(args.shard_dir)
    errors = []
    for rel in contract.get("required_outputs", []):
        p = shard / rel
        if not p.exists() or p.stat().st_size == 0:
            errors.append(f"missing/empty required output: {rel}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: shard outputs validate")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
