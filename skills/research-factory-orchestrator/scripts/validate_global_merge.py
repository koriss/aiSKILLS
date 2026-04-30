#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys

REQUIRED_OUTPUTS = [
    "global-sources.json",
    "global-claims.json",
    "global-evidence-cards.json",
    "global-citation-map.json",
    "global-coverage-matrix.json"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    args = ap.parse_args()
    root = Path(args.project_dir)
    errors = []
    for rel in REQUIRED_OUTPUTS:
        p = root / rel
        if not p.exists() or p.stat().st_size == 0:
            errors.append(f"missing/empty global merge artifact: {rel}")
        elif p.suffix == ".json":
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"bad json {rel}: {e}")
    mc = root / "merge-conflicts.json"
    if mc.exists():
        data = json.loads(mc.read_text(encoding="utf-8"))
        if data.get("open_high_conflicts", 0) > 0:
            errors.append("open high merge conflicts")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: global merge validates")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
