#!/usr/bin/env python3
"""Read validation-transcript.json and exit 0 iff validation passed (v18 legacy or v19)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    p = Path(args.run_dir) / "validation-transcript.json"
    if not p.is_file():
        print("missing validation-transcript.json", file=sys.stderr)
        return 1
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    if isinstance(o, dict) and "overall_pass" in o:
        ok = bool(o.get("overall_pass"))
    else:
        ok = str(o.get("status", "")).lower() == "pass"
    print(json.dumps({"passed": ok}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
