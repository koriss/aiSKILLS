#!/usr/bin/env python3
"""Detect absolute filesystem paths leaked into chat message bodies (F198)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


_PATTERNS = [
    re.compile(r"/tmp/"),
    re.compile(r"/home/"),
    re.compile(r"/opt/"),
    re.compile(r"/var/"),
    re.compile(r"/usr/"),
    re.compile(r"/root/"),
    re.compile(r"~/"),
    re.compile(r"^[A-Z]:\\", re.MULTILINE),
    re.compile(r"^\\\\", re.MULTILINE),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_no_local_paths_in_chat.py <run_dir>", file=sys.stderr)
        return 2
    rd = Path(sys.argv[1])
    hits = []
    for p in sorted((rd / "chat").glob("message-*.txt")) if (rd / "chat").is_dir() else []:
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in _PATTERNS:
            if pat.search(text):
                hits.append({"file": str(p.relative_to(rd)), "pattern": pat.pattern})
                break
    dm = {}
    if (rd / "delivery-manifest.json").is_file():
        dm = json.loads((rd / "delivery-manifest.json").read_text(encoding="utf-8"))
    if dm.get("local_paths_exposed") is True:
        hits.append({"delivery_manifest": "local_paths_exposed_true"})
    if hits:
        print(json.dumps({"status": "fail", "local_path_hits": hits}, ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
