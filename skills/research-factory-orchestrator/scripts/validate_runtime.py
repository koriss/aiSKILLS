#!/usr/bin/env python3
"""Validate a runtime directory produced by init_runtime / executor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = [
    "runtime-contract.json",
    "runtime-state.json",
    "queue.json",
    "artifact-manifest.json",
    "tool-registry.json",
    "logs/trace.jsonl",
    "logs/activity-history.html",
]


def _basic_html(s: str) -> bool:
    t = s.lower()
    return "<html" in t and "</html>" in t


def main() -> int:
    p = argparse.ArgumentParser(description="Validate runtime project directory")
    p.add_argument("--project-dir", required=True)
    args = p.parse_args()
    root = Path(args.project_dir).resolve()
    for rel in REQUIRED:
        f = root / rel
        if not f.is_file() or f.stat().st_size == 0:
            print(f"Missing or empty: {rel}", file=sys.stderr)
            return 1
    for name in ["runtime-contract.json", "runtime-state.json", "queue.json", "artifact-manifest.json", "tool-registry.json"]:
        json.loads((root / name).read_text(encoding="utf-8"))
    for html in root.rglob("*.html"):
        if html.stat().st_size and not _basic_html(html.read_text(encoding="utf-8", errors="ignore")):
            print(f"Invalid HTML: {html.relative_to(root)}", file=sys.stderr)
            return 1
    print("Runtime directory OK:", root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
