#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

TABLE = re.compile(r'^\s*\|.+\|\s*$', re.M)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("provider_payload")
    args = ap.parse_args()
    d = json.loads(Path(args.provider_payload).read_text(encoding="utf-8"))
    errors = []
    if not d.get("provider"):
        errors.append("missing provider")
    if not d.get("event_id"):
        errors.append("missing event_id")
    payload = d.get("payload", {})
    text = str(payload.get("text", ""))
    if payload.get("no_tables") is True and TABLE.search(text):
        errors.append("provider payload contains markdown table")
    if "/home/" in text or "/tmp/" in text:
        errors.append("provider payload contains local path")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: provider payload validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
