#!/usr/bin/env python3
from pathlib import Path
import argparse, runpy, sys
# The canonical package is built by runtime_job_worker before outbox file event OUT-0006.
# This wrapper exists for compatibility and executes a direct runtime package build by invoking worker internals via core module.
# Prefer: runtime_job_worker.py --execute-runtime
import importlib.util
core_path = Path(__file__).resolve().parent / 'rfo_v18_core.py'
spec = importlib.util.spec_from_file_location('rfo_v18_core', core_path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); args=ap.parse_args()
mod.build_package(Path(args.run_dir))
