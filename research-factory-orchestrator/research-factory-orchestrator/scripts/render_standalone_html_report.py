#!/usr/bin/env python3
"""Deprecated entrypoint — use ``scripts/rfo_render.py semantic-shell --run-dir …``."""

from __future__ import annotations

import sys

from rfo_render import main as rfo_render_main


if __name__ == "__main__":
    tail = sys.argv[1:]
    if len(tail) == 1 and not tail[0].startswith("-"):
        raise SystemExit(rfo_render_main(["semantic-shell", "--run-dir", tail[0]]))
    raise SystemExit(rfo_render_main(["semantic-shell"] + tail))
