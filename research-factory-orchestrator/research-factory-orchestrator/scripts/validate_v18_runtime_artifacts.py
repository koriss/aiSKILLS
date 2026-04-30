#!/usr/bin/env python3
from pathlib import Path
import importlib.util, argparse
core_path = Path(__file__).resolve().parent / 'rfo_v18_core.py'
spec = importlib.util.spec_from_file_location('rfo_v18_core', core_path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True); args=ap.parse_args()
raise SystemExit(mod.validate(args.run_dir))
