#!/usr/bin/env python3
"""
Clean-install smoke (v19.1): unzip ``release-artifacts/research-factory-orchestrator-*.zip``
into a temp dir, then run ``validate_skill``, ``check_schema_drift``, and
``run_core_validators`` on ``tests/fixtures/v19/good/mvr_minimal_valid`` from that tree.

Optional: ``RFO_RELEASE_ZIP_PATH`` points to a specific zip.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _find_release_zip(root: Path) -> Path | None:
    env = os.environ.get("RFO_RELEASE_ZIP_PATH", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p
    art = root / "release-artifacts"
    if not art.is_dir():
        return None
    zips = sorted(art.glob("research-factory-orchestrator-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def main() -> int:
    py = sys.executable
    zip_p = _find_release_zip(ROOT)
    if not zip_p or not zip_p.is_file():
        print(json.dumps({"error": "missing_release_zip", "detail": str(ROOT / "release-artifacts")}, ensure_ascii=False), file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="rfo-clean-install-") as td:
        ext = Path(td) / "extracted"
        ext.mkdir()
        with zipfile.ZipFile(zip_p, "r") as zf:
            zf.extractall(ext)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        for rel in ("scripts/validate_skill.py", "scripts/check_schema_drift.py"):
            sp = ext / rel
            if not sp.is_file():
                print(json.dumps({"error": "missing_script_in_zip", "path": str(rel)}, ensure_ascii=False), file=sys.stderr)
                return 1
            p = subprocess.run([py, "-S", str(sp)], cwd=str(ext), capture_output=True, text=True, timeout=600, env=env)
            if p.returncode != 0:
                print(f"[clean_install] {rel} rc={p.returncode}", file=sys.stderr)
                print((p.stderr or "")[-3000:], file=sys.stderr)
                return 1

        fix_src = ext / "tests" / "fixtures" / "v19" / "good" / "mvr_minimal_valid"
        if not fix_src.is_dir():
            print(json.dumps({"error": "missing_fixture_in_zip", "path": str(fix_src.relative_to(ext))}, ensure_ascii=False), file=sys.stderr)
            return 1
        run_dir = Path(td) / "run"
        _copy_fixture(fix_src, run_dir)
        rc_script = ext / "scripts" / "run_core_validators.py"
        if not rc_script.is_file():
            print(json.dumps({"error": "missing_run_core_in_zip"}, ensure_ascii=False), file=sys.stderr)
            return 1
        pr = subprocess.run(
            [py, "-S", str(rc_script), "--run-dir", str(run_dir), "--profile", "mvr"],
            cwd=str(ext),
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        if pr.returncode != 0:
            print(f"[clean_install] run_core_validators rc={pr.returncode}", file=sys.stderr)
            print((pr.stderr or "")[-3000:], file=sys.stderr)
            return 1
        trp = run_dir / "validation-transcript.json"
        if not trp.is_file():
            print("[clean_install] missing validation-transcript.json", file=sys.stderr)
            return 1
        try:
            tr = json.loads(trp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[clean_install] bad transcript json: {e}", file=sys.stderr)
            return 1
        if tr.get("overall_pass") is not True:
            print(json.dumps({"error": "clean_install_fixture_not_pass", "transcript": str(trp)}, ensure_ascii=False), file=sys.stderr)
            return 1

    print(json.dumps({"status": "ok", "zip": str(zip_p)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
