#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    plan = json.loads((root / "subagent-plan.json").read_text(encoding="utf-8"))
    errors = []
    for a in plan.get("assignments", []):
        if a.get("status") != "completed":
            continue
        sa = a.get("subagent_id")
        for rel in a.get("required_outputs", []):
            p = root / "subagents" / sa / rel
            if not p.exists():
                errors.append(f"{sa}: completed worker missing output {rel}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: worker required outputs validate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
