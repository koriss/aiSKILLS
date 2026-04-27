#!/usr/bin/env python3
import subprocess
from pathlib import Path

def main() -> None:
    base = Path(__file__).resolve().parents[1]
    req = base / "examples" / "example-military-bases.md"
    out = base / "examples" / "generated-military-bases-runtime"
    cmd = [
        "python3", str(base / "scripts" / "compile_runtime.py"),
        "--request-file", str(req),
        "--project-dir", str(out),
        "--output-formats", "html", "json",
        "--queue-mode", "auto",
        "--depth-level", "deep",
        "--autonomy-mode", "full_auto",
        "--force",
    ]
    subprocess.run(cmd, check=True)
    print(f"Sample runtime generated at {out}")

if __name__ == "__main__":
    main()
