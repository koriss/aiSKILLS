"""Canonical RFO skill version from runtime/version.json (single source of truth)."""
from __future__ import annotations

import json
from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent / "version.json"


def _load_skill_version() -> str:
    if not _VERSION_FILE.is_file():
        return "18.5.0-unknown"
    try:
        meta = json.loads(_VERSION_FILE.read_text(encoding="utf-8"))
        return str(meta.get("skill_version") or meta.get("version") or "18.5.0-unknown")
    except Exception:
        return "18.5.0-unknown"


VERSION = _load_skill_version()
