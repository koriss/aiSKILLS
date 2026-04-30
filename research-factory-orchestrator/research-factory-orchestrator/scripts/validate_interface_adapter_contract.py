#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir")
    args = ap.parse_args()
    p = Path(args.skill_dir) / "contracts" / "interface-adapter-contract.json"
    if not p.exists():
        print("missing interface-adapter-contract.json", file=sys.stderr)
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    errors = []
    for f in ["supported_interfaces", "supported_providers", "required_adapter_outputs", "forbidden"]:
        if not d.get(f):
            errors.append(f"missing/empty {f}")
    for provider in ["telegram", "cli"]:
        if provider not in d.get("supported_providers", []):
            errors.append(f"{provider} provider not declared")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: interface adapter contract validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
