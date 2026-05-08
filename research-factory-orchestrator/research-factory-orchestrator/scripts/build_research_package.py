#!/usr/bin/env python3
"""Compatibility wrapper for explicit package rebuild by run_dir."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.worker_impl import build_package

ap = argparse.ArgumentParser()
ap.add_argument("--run-dir", required=True)
args = ap.parse_args()
build_package(Path(args.run_dir))
