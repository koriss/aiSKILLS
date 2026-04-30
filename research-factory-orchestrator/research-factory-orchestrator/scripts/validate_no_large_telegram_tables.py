#!/usr/bin/env python3
from pathlib import Path
import argparse, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message_file")
    args = ap.parse_args()
    text = Path(args.message_file).read_text(encoding="utf-8", errors="replace")
    errors = []

    rows = [line for line in text.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if rows:
        if len(rows) > 5:
            errors.append(f"telegram table has too many rows: {len(rows)} > 5")
        max_cols = max(line.count("|") - 1 for line in rows)
        if max_cols > 3:
            errors.append(f"telegram table has too many columns: {max_cols} > 3")
        if any(word in text.lower() for word in ["source registry", "coverage matrix", "evidence map", "fact-check table"]):
            errors.append("large analytical table detected in telegram message")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: no large telegram tables")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
