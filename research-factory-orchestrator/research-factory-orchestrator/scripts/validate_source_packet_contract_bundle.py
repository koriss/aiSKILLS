#!/usr/bin/env python3
"""Anti-regression: every committed source-packet fixture + template validates (stdlib subprocess)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    validate = root / "scripts" / "rfo_validate_source_packet.py"
    violations: list[str] = []

    fix_dir = root / "tests" / "fixtures" / "source_packets"
    for p in sorted(fix_dir.glob("*.json")):
        cmd = [py, "-S", str(validate), "--source-packet", str(p)]
        r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stdout or r.stderr or "").strip()[:400]
            violations.append(f"fixture:{p.name}:exit_{r.returncode}:{tail}")

    tmpl_dir = root / "templates"
    if tmpl_dir.is_dir():
        for p in sorted(tmpl_dir.glob("source-packet*.json")):
            cmd = [
                py,
                "-S",
                str(validate),
                "--source-packet",
                str(p),
                "--template-mode",
            ]
            r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
            if r.returncode != 0:
                tail = (r.stdout or r.stderr or "").strip()[:400]
                violations.append(f"template:{p.name}:exit_{r.returncode}:{tail}")

    print(
        json.dumps(
            {"validator": "validate_source_packet_contract_bundle", "violations": violations},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
