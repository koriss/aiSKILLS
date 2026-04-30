#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workplan")
    args = ap.parse_args()
    data = json.loads(Path(args.workplan).read_text(encoding="utf-8"))
    errors = []
    units = data.get("work_units", [])
    if not units:
        errors.append("work_units empty")
    ids = set()
    for u in units:
        wid = u.get("work_unit_id")
        if not wid:
            errors.append("work unit missing work_unit_id")
        elif wid in ids:
            errors.append(f"duplicate work_unit_id: {wid}")
        ids.add(wid)
        for k in ["objective","coverage_categories","required_outputs","validators","merge_target","done_definition"]:
            if not u.get(k):
                errors.append(f"{wid}: missing/empty {k}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: workplan validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
