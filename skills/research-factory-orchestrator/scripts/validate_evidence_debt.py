#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence_debt")
    args = ap.parse_args()
    data = json.loads(Path(args.evidence_debt).read_text(encoding="utf-8"))
    errors = []
    if data.get("open_high_severity_count", 0) > 0:
        errors.append("open high-severity evidence debt exists")
    for d in data.get("debts", []):
        if d.get("severity") == "high" and d.get("status") == "open":
            errors.append(f"open high debt: {d.get('debt_id')}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no open high-severity evidence debt")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
