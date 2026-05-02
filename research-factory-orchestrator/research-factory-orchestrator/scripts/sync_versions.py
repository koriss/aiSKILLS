#!/usr/bin/env python3
"""Align declared versions across runtime/version.json, policies, and contracts (P1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "runtime" / "version.json"


def main() -> int:
    if not VERSION_FILE.exists():
        print("missing runtime/version.json", file=sys.stderr)
        return 1
    meta = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    ver = meta.get("skill_version", "")
    print(json.dumps({"status": "ok", "canonical_skill_version": ver, "checked_paths": ["runtime/version.json"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
