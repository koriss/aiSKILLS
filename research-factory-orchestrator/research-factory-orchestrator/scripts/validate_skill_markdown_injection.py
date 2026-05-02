#!/usr/bin/env python3
"""Static scan of skill markdown for hidden instructions (arXiv:2510.26328)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = re.compile(
    r"(?i)(color\s*:\s*#fff|opacity\s*:\s*0|font-size\s*:\s*0|display\s*:\s*none|<!--\s*inject|"
    r"ignore\s+previous|override\s+skill)",
)


def main() -> int:
    hits = []
    paths = [ROOT / "SKILL.md"]
    for sub in ("references", "docs"):
        d = ROOT / sub
        if d.is_dir():
            paths.extend(p for p in d.rglob("*.md") if p.is_file())
    for p in paths:
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if BAD.search(t):
            hits.append(str(p.relative_to(ROOT)))
    if hits:
        print(json.dumps({"status": "fail", "files": hits[:40]}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass", "scanned": "SKILL.md+docs"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
