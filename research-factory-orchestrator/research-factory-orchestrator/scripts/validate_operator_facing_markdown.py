#!/usr/bin/env python3
"""Guardrail: operator-facing SKILL*.md must not advertise alternate bridge CLIs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FORBIDDEN_SUBSTRING = "python3 -S scripts/run_rfo_with_web_search.py"

# Operator-facing must not imply cryptographic / proof-of-fetch retrieval without agent-attested framing.
_MARKETING_PATTERNS = (
    (re.compile(r"\bverified\s+retrieval\b", re.I), "verified_retrieval"),
    (re.compile(r"\bproof-of-fetch\b", re.I), "proof-of-fetch"),
    (re.compile(r"\bcryptographically\s+verified\b", re.I), "cryptographically_verified"),
)


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
        lines = text.splitlines()
        for i, line in enumerate(lines):
            low = line.lower()
            if "agent-attested" in low or "agent attested" in low:
                continue
            for rx, tag in _MARKETING_PATTERNS:
                if rx.search(line):
                    errs.append(f"{name}:marketing_phrase_without_agent_attested:{tag}:L{i+1}")
    return errs


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errs = validate(root)
    print(json.dumps({"validator": "validate_operator_facing_markdown", "errors": errs}, ensure_ascii=False, indent=2))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
