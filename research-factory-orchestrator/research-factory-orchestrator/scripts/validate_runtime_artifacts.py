#!/usr/bin/env python3
"""Run core runtime validate(run_dir) via rfo_runtime_core (v19)."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

core_path = Path(__file__).resolve().parent / "rfo_runtime_core.py"
spec = importlib.util.spec_from_file_location("rfo_runtime_core", core_path)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)
ap = argparse.ArgumentParser()
ap.add_argument("--run-dir", required=True)
args = ap.parse_args()
raise SystemExit(mod.validate(args.run_dir))
