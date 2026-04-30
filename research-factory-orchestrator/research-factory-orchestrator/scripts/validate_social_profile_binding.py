#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profiles_json")
    args = ap.parse_args()
    data = json.loads(Path(args.profiles_json).read_text(encoding="utf-8"))
    profiles = data.get("profiles") or data.get("nodes") or (data if isinstance(data, list) else [])
    errors = []
    for p in profiles:
        if p.get("status") == "confirmed" and not p.get("strong_binding_signals"):
            errors.append(f"{p.get('profile_id','?')}: confirmed without strong binding signals")
        if p.get("status") == "confirmed" and p.get("name_only_match"):
            errors.append(f"{p.get('profile_id','?')}: name-only match promoted to confirmed")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: social profile binding validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
