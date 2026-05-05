#!/usr/bin/env python3
"""
Deterministic replay smoke (v19.1): copy ``good/mvr_minimal_valid`` → temp run-dir,
``validate()`` twice with identical B1 env knobs; normalized ``validation-transcript.json``
must match (failure code DETERMINISTIC-DRIFT).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "v19" / "good" / "mvr_minimal_valid"

_TRANSCRIPT_STRIP_KEYS: frozenset[str] = frozenset({"created_at"})


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def _normalize_transcript_bytes(raw: bytes) -> bytes:
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        return raw
    if not isinstance(obj, dict):
        return raw
    slim = {k: v for k, v in obj.items() if k not in _TRANSCRIPT_STRIP_KEYS}
    return (json.dumps(slim, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_run_dir(py: str, run_dir: Path, env: dict[str, str]) -> int:
    code = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "from runtime.validate_impl import validate; "
        "sys.exit(validate(Path(sys.argv[1])))"
    )
    p = subprocess.run(
        [py, "-S", "-c", code, str(run_dir)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    if p.returncode != 0:
        print(f"[det_replay] validate rc={p.returncode}", file=sys.stderr)
        print((p.stderr or "")[-3000:], file=sys.stderr)
    return p.returncode


def main() -> int:
    if not FIXTURE.is_dir():
        print(f"[det_replay] missing fixture {FIXTURE}", file=sys.stderr)
        return 1
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="rfo-det-replay-") as td:
        run_dir = Path(td) / "run"
        _copy_fixture(FIXTURE, run_dir)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "RFO_V19_PROFILE": "mvr"}
        env["RFO_FIXED_TIME"] = "2026-05-05T12:00:00Z"
        env["RFO_DETERMINISTIC_IDS"] = "1"
        env["RFO_ID_SALT"] = "smoke_deterministic_replay_v19"
        if _validate_run_dir(py, run_dir, env) != 0:
            print("[det_replay] first validate failed", file=sys.stderr)
            return 1
        tp = run_dir / "validation-transcript.json"
        if not tp.is_file():
            print("[det_replay] missing validation-transcript.json", file=sys.stderr)
            return 1
        first = _normalize_transcript_bytes(tp.read_bytes())
        if _validate_run_dir(py, run_dir, env) != 0:
            print("[det_replay] second validate failed", file=sys.stderr)
            return 1
        second = _normalize_transcript_bytes(tp.read_bytes())
        if first != second:
            print(
                json.dumps(
                    {
                        "error": "DETERMINISTIC-DRIFT",
                        "detail": "validation-transcript.json differs between two validates under fixed env",
                        "len_first": len(first),
                        "len_second": len(second),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 1
        print(json.dumps({"status": "ok", "run_dir": str(run_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
