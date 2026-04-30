#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("identity_candidates")
    args = ap.parse_args()
    data = json.loads(Path(args.identity_candidates).read_text(encoding="utf-8"))
    candidates = data.get("candidates", data if isinstance(data, list) else [])
    errors = []
    for c in candidates:
        status = c.get("identity_status")
        used = c.get("used_in_report", False)
        if used and status not in ["confirmed", "probable"]:
            errors.append(f"profile used but not confirmed/probable: {c.get('candidate_id')}")
        if status in ["confirmed", "probable"] and not c.get("hard_signals"):
            errors.append(f"confirmed/probable profile has no hard signals: {c.get('candidate_id')}")
        if status in ["confirmed", "probable"] and c.get("critical_conflicts"):
            errors.append(f"confirmed/probable profile has conflicts: {c.get('candidate_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: social profile linkage validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
