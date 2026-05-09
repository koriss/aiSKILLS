#!/usr/bin/env python3
"""Deprecated entrypoint — use ``scripts/rfo_render.py canonical --run-dir …``."""

from __future__ import annotations

import sys

from rfo_render import main as rfo_render_main


if __name__ == "__main__":
    raise SystemExit(rfo_render_main(["canonical"] + sys.argv[1:]))
