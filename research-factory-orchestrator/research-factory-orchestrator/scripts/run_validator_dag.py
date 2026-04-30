#!/usr/bin/env python3
from pathlib import Path
import runpy, sys
core = Path(__file__).resolve().parent / 'rfo_v18_core.py'
sys.argv = [str(core), 'validate'] + sys.argv[1:]
runpy.run_path(str(core), run_name='__main__')
