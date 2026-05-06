#!/usr/bin/env python3
"""Phase 5 matrix umbrella (REQUIRED_GATES alias for v19.2.0 integration smokes).

Delegates to ``_smoke_v19_2_integration.py`` — single source of truth for the
T5.1–T5.11 scenario bundle implemented there.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = subprocess.run(
        [sys.executable, "-S", str(ROOT / "scripts" / "_smoke_v19_2_integration.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT)},
    )
    tail = (p.stdout or "").strip().splitlines()
    inner = {}
    if tail:
        try:
            inner = json.loads(tail[-1])
        except Exception:
            inner = {}
    ok = p.returncode == 0 and bool(inner.get("passed"))
    print(
        json.dumps(
            {
                "smoke_id": "_smoke_v19_2_phase5_matrix",
                "schema_version": "v19.0",
                "passed": ok,
                "delegated": "_smoke_v19_2_integration",
                "integration": inner,
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
