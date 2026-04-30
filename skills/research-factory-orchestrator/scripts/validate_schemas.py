#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("schemas_dir")
    args=ap.parse_args()
    errors=[]
    for f in Path(args.schemas_dir).glob("*.schema.json"):
        try:
            data=json.loads(f.read_text(encoding="utf-8"))
            for k in ["$schema","type","properties"]:
                if k not in data:
                    errors.append(f"{f.name}: missing {k}")
        except Exception as e:
            errors.append(f"{f.name}: {e}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: schemas validate")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
