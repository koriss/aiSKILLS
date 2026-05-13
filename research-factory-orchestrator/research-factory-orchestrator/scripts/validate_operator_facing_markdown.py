#!/usr/bin/env python3
"""Guardrail: operator-facing SKILL*.md must not advertise alternate bridge CLIs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

FORBIDDEN_SUBSTRING = "python3 -S scripts/run_rfo_with_web_search.py"


def validate(root: Path) -> list[str]:
    errs: list[str] = []
    for name in ("SKILL.md", "SKILL-core.md"):
        path = root / name
        if not path.is_file():
            errs.append(f"missing_operator_facing:{name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if FORBIDDEN_SUBSTRING in text:
            errs.append(f"{name}:forbidden_operator_copy_paste_bridge_cli")
    return errs


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errs = validate(root)
    print(json.dumps({"validator": "validate_operator_facing_markdown", "errors": errs}, ensure_ascii=False, indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
