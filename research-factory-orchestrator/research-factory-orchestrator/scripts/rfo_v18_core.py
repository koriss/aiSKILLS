#!/usr/bin/env python3
"""Deprecated compatibility shim — use ``scripts/rfo_runtime_core.py`` (RFO v19.2.0)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
