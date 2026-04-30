#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("normalized_command")
    args = ap.parse_args()
    d = json.loads(Path(args.normalized_command).read_text(encoding="utf-8"))
    errors = []
    for f in ["command_id","interface","provider","conversation_id","message_id","user_id","command","task","delivery_constraints"]:
        if f not in d:
            errors.append(f"missing {f}")
    if not d.get("task"):
        errors.append("empty task")
    dc = d.get("delivery_constraints", {})
    if dc.get("no_tables") is not True:
        errors.append("delivery_constraints.no_tables must be true")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: normalized command validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
