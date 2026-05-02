#!/usr/bin/env python3
"""B3: full v19 validators chain on pristine empty run-dir → expected fail + validation_failed state."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_validate(rd: Path) -> int:
    env = {**os.environ, "RFO_V19_PROFILE": "mvr", "PYTHONDONTWRITEBYTECODE": "1"}
    code = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "from runtime.validate_impl import validate; "
        "sys.exit(validate(Path(sys.argv[1])))"
    )
    p = subprocess.run(
        [sys.executable, "-S", "-c", code, str(rd)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return p.returncode


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rfo-pristine-smoke-") as td:
        rd = Path(td)
        rc = _run_validate(rd)
        if rc == 0:
            print(json.dumps({"status": "fail", "detail": "expected non-zero rc on pristine empty run-dir"}, ensure_ascii=False))
            return 1
        rs = json.loads((rd / "runtime-status.json").read_text(encoding="utf-8"))
        if rs.get("state") != "validation_failed":
            print(
                json.dumps(
                    {"status": "fail", "detail": f"expected state validation_failed got {rs.get('state')!r}"},
                    ensure_ascii=False,
                )
            )
            return 1
    print(json.dumps({"status": "pass", "detail": "pristine v19 validate failed closed as expected"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
