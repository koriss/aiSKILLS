"""Fixed-argv subprocess runner for operator Telegram tooling."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_module(module: str, argv: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Invoke ``python -S -m <module>`` with *exactly* the provided argv tail (no shell)."""
    cmd = [sys.executable, "-S", "-m", module, *argv]
    return subprocess.run(cmd, cwd=str(cwd or Path.cwd()), capture_output=True, text=True, timeout=timeout, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
