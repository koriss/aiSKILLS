#!/usr/bin/env python3
"""Run validate_release_report.py against tests/fixtures/v19/release_bad/* (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL_BAD = ROOT / "tests" / "fixtures" / "v19" / "release_bad"
FORBIDDEN = frozenset({"validation-transcript.json", "validation-profile-used.json"})


def _fixture_hygiene(d: Path) -> list[str]:
    bad: list[str] = []
    for p in d.rglob("*"):
        if p.is_file() and p.name in FORBIDDEN:
            bad.append(str(p.relative_to(d)))
    return bad


def _fix_transcript_sha(tp: Path) -> None:
    data = json.loads(tp.read_text(encoding="utf-8"))
    body = {k: v for k, v in data.items() if k != "transcript_sha256"}
    h = hashlib.sha256()
    h.update(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    data["transcript_sha256"] = h.hexdigest()
    tp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    py = sys.executable
    errs: list[str] = []
    if not REL_BAD.is_dir():
        print(json.dumps({"status": "fail", "errors": ["missing release_bad dir"]}, ensure_ascii=False))
        return 1
    for fx in sorted(REL_BAD.iterdir()):
        if not fx.is_dir():
            continue
        name = fx.name
        fh = _fixture_hygiene(fx)
        if fh:
            errs.append(f"{name}: FIXTURE-HYGIENE-VIOLATION {fh}")
            continue
        exp_path = fx / "expected.json"
        if not exp_path.is_file():
            errs.append(f"{name}: FIXTURE-MISSING-EXPECTED")
            continue
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        if not isinstance(exp, dict):
            errs.append(f"{name}: bad expected.json")
            continue
        exp_rc = int(exp.get("expected_rc", 1))
        exp_checker = str(exp.get("expected_checker") or "validate_release_report")
        exp_codes = [str(c) for c in (exp.get("expected_issue_codes") or []) if c]
        with tempfile.TemporaryDirectory(prefix="rfo-rel-bad-", ignore_cleanup_errors=True) as td:
            work = Path(td)
            t_src = fx / "release-transcript.json"
            r_src = fx / "release-report.md"
            if not t_src.is_file():
                errs.append(f"{name}: missing release-transcript.json")
                continue
            t_dst = work / "release-transcript.json"
            shutil.copy2(t_src, t_dst)
            _fix_transcript_sha(t_dst)
            cmd = [py, "-S", str(ROOT / "scripts" / "validate_release_report.py"), "--transcript", str(t_dst)]
            if r_src.is_file():
                cmd.append(str(r_src))
            pr = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            if pr.returncode != exp_rc:
                errs.append(f"{name}: want rc={exp_rc} got {pr.returncode} stderr={(pr.stderr or '')[-400:]}")
                continue
            if exp_rc != 0 and exp_codes:
                last = (pr.stdout or "").strip().splitlines()[-1] if (pr.stdout or "").strip() else ""
                try:
                    jo = json.loads(last)
                except Exception:
                    jo = {}
                ic = str(jo.get("issue_code") or "")
                if ic and exp_codes and ic not in exp_codes:
                    errs.append(f"{name}: issue_code {ic!r} not in expected {exp_codes}")
                if not ic and exp_checker == "validate_release_report":
                    if not any(c in (pr.stdout or "") for c in exp_codes):
                        if exp_codes[0] not in (pr.stdout or ""):
                            errs.append(f"{name}: expected issue hint {exp_codes} in stdout")
            if exp_rc == 0 and exp_checker != "validate_release_report":
                errs.append(f"{name}: expected_checker not implemented for rc=0")
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
