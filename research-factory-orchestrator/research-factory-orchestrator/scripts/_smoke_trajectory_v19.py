#!/usr/bin/env python3
"""
Trajectory smoke (v19.1): verify ``run-events.jsonl`` contract — V1→V6 ``validator.started``
order with paired ``validator.finished``, and ``rollback.triggered`` when validation fails.

Failure code printed on stderr: TRAJECTORY-SKIP.
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

CHAIN = [
    "validate_artifact_schema",
    "validate_traceability",
    "validate_source_quality",
    "validate_claim_status",
    "validate_final_answer",
    "validate_delivery_truth",
]

GOOD_FIX = ROOT / "tests" / "fixtures" / "v19" / "good" / "mvr_minimal_valid"
BAD_FIX = ROOT / "tests" / "fixtures" / "v19" / "bad" / "claim_without_evidence"


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def _run_validate(py: str, run_dir: Path, env: dict[str, str]) -> int:
    code = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "from runtime.validate_impl import validate; "
        "sys.exit(validate(Path(sys.argv[1])))"
    )
    return subprocess.run(
        [py, "-S", "-c", code, str(run_dir)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    ).returncode


def _load_events(run_dir: Path) -> list[dict[str, object]]:
    p = run_dir / "run-events.jsonl"
    if not p.is_file():
        return []
    out: list[dict[str, object]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            if isinstance(o, dict):
                out.append(o)
        except Exception:
            continue
    return out


def _check_trajectory_good(run_dir: Path) -> tuple[bool, str]:
    evs = _load_events(run_dir)
    started: list[str] = []
    finished: list[str] = []
    stack: list[str] = []
    for e in evs:
        ev = str(e.get("event") or "")
        vid = str(e.get("validator_id") or "")
        if ev == "validator.started":
            if stack:
                return False, f"nested validator.started for {vid!r} while {stack[-1]!r} unfinished"
            if vid not in CHAIN:
                return False, f"unexpected started validator_id {vid!r}"
            started.append(vid)
            stack.append(vid)
        elif ev == "validator.finished":
            if not stack or stack[-1] != vid:
                return False, f"validator.finished for {vid!r} without matching started (stack={stack!r})"
            stack.pop()
            finished.append(vid)
    if stack:
        return False, f"unfinished validators {stack!r}"
    started_chain = [v for v in started if v in CHAIN]
    if started_chain != CHAIN:
        return False, f"want started order {CHAIN} got {started_chain}"
    if finished != CHAIN:
        return False, f"want finished order {CHAIN} got {finished}"
    return True, ""


def main() -> int:
    py = sys.executable
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "RFO_V19_PROFILE": "mvr"}

    if not GOOD_FIX.is_dir() or not BAD_FIX.is_dir():
        print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "missing fixtures"}, ensure_ascii=False), file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="rfo-trj-good-") as td:
        rd = Path(td) / "run"
        _copy_fixture(GOOD_FIX, rd)
        if _run_validate(py, rd, env) != 0:
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "good fixture validate failed"}, ensure_ascii=False), file=sys.stderr)
            return 1
        ok, msg = _check_trajectory_good(rd)
        if not ok:
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": msg}, ensure_ascii=False), file=sys.stderr)
            return 1
        tr = json.loads((rd / "validation-transcript.json").read_text(encoding="utf-8"))
        if tr.get("overall_pass") is not True:
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "expected overall_pass true"}, ensure_ascii=False), file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="rfo-trj-bad-") as td2:
        rd2 = Path(td2) / "run"
        _copy_fixture(BAD_FIX, rd2)
        if _run_validate(py, rd2, env) == 0:
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "bad fixture expected validate rc!=0"}, ensure_ascii=False), file=sys.stderr)
            return 1
        tr2 = json.loads((rd2 / "validation-transcript.json").read_text(encoding="utf-8"))
        if tr2.get("overall_pass") is not False:
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "expected overall_pass false"}, ensure_ascii=False), file=sys.stderr)
            return 1
        if not any(e.get("event") == "rollback.triggered" for e in _load_events(rd2)):
            print(json.dumps({"error": "TRAJECTORY-SKIP", "detail": "missing rollback.triggered on fail path"}, ensure_ascii=False), file=sys.stderr)
            return 1

    print(json.dumps({"status": "ok"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
