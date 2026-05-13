#!/usr/bin/env python3
"""
Canonical production façade for the RFO relay + queue bridge.

Loads and runs ``main()`` from ``scripts/run_rfo_with_web_search.py`` with the **same
argv and exit code**. **All new docs, compose, and native slash handlers should
invoke this path** (`python3 -S scripts/rfo_execute.py …`).

The implementation module remains ``run_rfo_with_web_search.py`` (do not fork
semantics). ``scripts/run_rfo_full_research.py`` is **retired as an operator
entrypoint**: running it prints a fatal hint to use ``rfo_execute.py`` and exits
**2**. Test helpers live in ``runtime/standalone_relay_driver.py``. See
``docs/runtime-paths.md``.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    bridge = here / "run_rfo_with_web_search.py"
    if not bridge.is_file():
        print(f"[fatal] bridge script missing: {bridge}", file=sys.stderr)
        return 2
    spec = importlib.util.spec_from_file_location("_rfo_relay_bridge", bridge)
    if spec is None or spec.loader is None:
        print("[fatal] could not load bridge module spec", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
