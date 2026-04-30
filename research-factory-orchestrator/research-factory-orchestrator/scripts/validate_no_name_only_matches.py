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
        signals = c.get("hard_signals", [])
        soft = c.get("soft_signals", [])
        status = c.get("identity_status")
        if status in ["confirmed", "probable"] and not signals:
            errors.append(f"name/soft-only profile upgraded to {status}: {c.get('candidate_id')}")
        if c.get("used_in_report") and not signals:
            errors.append(f"profile used in report without hard signal: {c.get('candidate_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no name-only matches used")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
