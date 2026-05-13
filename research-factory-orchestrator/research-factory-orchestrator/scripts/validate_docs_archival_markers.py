#!/usr/bin/env python3
"""Ensure ``docs/analytics/README.md`` carries the archival root marker (subtree policy)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

MARKER = "ARCHIVAL_CONTEXT_ONLY"


def validate(root: Path) -> list[str]:
    errs: list[str] = []
    readme = root / "docs" / "analytics" / "README.md"
    if not readme.is_file():
        errs.append("docs_archival:missing_docs_analytics_readme")
        return errs
    text = readme.read_text(encoding="utf-8", errors="replace")
    if MARKER not in text:
        errs.append("docs_archival:readme_missing_marker")
    return errs


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errs = validate(root)
    print(json.dumps({"validator": "validate_docs_archival_markers", "errors": errs}, ensure_ascii=False, indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
