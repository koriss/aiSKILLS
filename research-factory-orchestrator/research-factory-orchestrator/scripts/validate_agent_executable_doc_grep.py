#!/usr/bin/env python3
"""Anti-regression: operator docs must not copy-paste the bridge as the research CLI."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Operator copy-paste of the implementation module as the primary launcher.
_BAD_BRIDGE = re.compile(r'python3\s+-S\s+scripts/run_rfo_with_web_search\.py(?:\s|")')


def validate(root: Path) -> list[str]:
    errs: list[str] = []
    for rel in ("SKILL.md", "SKILL-core.md", "docs/runtime-paths.md"):
        p = root / rel
        if not p.is_file():
            errs.append(f"agent_executable_docgrep:missing_file:{rel}")
            continue
        text = p.read_text(encoding="utf-8")
        if _BAD_BRIDGE.search(text):
            errs.append(f"agent_executable_docgrep:copy_paste_bridge_cli:{rel}")
    plan = root / "docs/plans/PLAN-rfo-agent-executable-single-behavior.md"
    if not plan.is_file():
        errs.append("agent_executable_docgrep:missing_plan:docs/plans/PLAN-rfo-agent-executable-single-behavior.md")
    return errs


def main() -> int:
    errs = validate(ROOT)
    print(json.dumps({"validator": "validate_agent_executable_doc_grep", "errors": errs}, indent=2, ensure_ascii=False))
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
