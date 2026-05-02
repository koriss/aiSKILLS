#!/usr/bin/env python3
"""Run all v19 good/bad fixtures through run_core_validators; assert expected.json (stdlib only)."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IN_FIXTURES = frozenset(
    {
        "validation-transcript.json",
        "validation-profile-used.json",
        "runtime-status.json",
        "release-validation-transcript.json",
    }
)
GOOD = ROOT / "tests" / "fixtures" / "v19" / "good"
BAD = ROOT / "tests" / "fixtures" / "v19" / "bad"


def _forbidden_paths(fixture_dir: Path) -> list[str]:
    bad: list[str] = []
    for p in fixture_dir.rglob("*"):
        if p.is_file() and p.name in FORBIDDEN_IN_FIXTURES:
            bad.append(str(p.relative_to(fixture_dir)))
    return bad


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def _parse_transcript(run_dir: Path) -> dict[str, object] | None:
    p = run_dir / "validation-transcript.json"
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def _issue_codes_from_validator(v: dict[str, object]) -> set[str]:
    out: set[str] = set()
    for it in v.get("issues") or []:
        if isinstance(it, dict) and it.get("code"):
            out.add(str(it["code"]))
    return out


def _run_one(fixture_dir: Path, py: str, profile: str) -> tuple[int, dict[str, object] | None, str]:
    with tempfile.TemporaryDirectory(prefix="rfo-v19-suite-", ignore_cleanup_errors=True) as td:
        tmp = Path(td) / "run"
        _copy_fixture(fixture_dir, tmp)
        pr = subprocess.run(
            [py, "-S", str(ROOT / "scripts" / "run_core_validators.py"), "--run-dir", str(tmp), "--profile", profile],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        tr = _parse_transcript(tmp)
        return pr.returncode, tr, (pr.stdout or "") + "\n" + (pr.stderr or "")


def _check_expected(
    name: str,
    rc: int,
    tr: dict[str, object] | None,
    exp: dict[str, object],
    raw_out: str,
) -> list[str]:
    errs: list[str] = []
    exp_rc = int(exp.get("expected_rc", 0))
    if rc != exp_rc:
        errs.append(f"{name}: want rc={exp_rc} got {rc}")
    allow_prior = bool(exp.get("allow_prior_fail", False))
    exp_val = str(exp.get("expected_validator") or "")
    exp_codes = [str(c) for c in (exp.get("expected_issue_codes") or []) if c]
    vals = [v for v in (tr or {}).get("validators") or [] if isinstance(v, dict)]
    if exp_rc == 0:
        if tr and tr.get("overall_pass") is not True:
            errs.append(f"{name}: expected pass but overall_pass is not true")
        if tr and str(tr.get("status") or "") != "pass":
            errs.append(f"{name}: want top-level status pass got {tr.get('status')!r}")
        return errs
    if not tr:
        errs.append(f"{name}: missing transcript after run stderr={raw_out[-500:]}")
        return errs
    fail_idxs = [i for i, v in enumerate(vals) if str(v.get("status") or "") in ("fail", "crash")]
    if not fail_idxs:
        errs.append(f"{name}: expected failure but no validator status fail/crash")
        return errs
    if not allow_prior:
        first_i = fail_idxs[0]
        for i, v in enumerate(vals):
            st = str(v.get("status") or "")
            if st in ("fail", "crash") and i < first_i:
                errs.append(f"{name}: validator at {i} failed before expected first failure")
                break
        first = vals[first_i]
        vid = str(first.get("validator_id") or "")
        if vid != exp_val:
            errs.append(f"{name}: want first_failed_validator={exp_val} got {vid}")
        icodes = _issue_codes_from_validator(first)
        for c in exp_codes:
            if c not in icodes:
                errs.append(f"{name}: missing issue code {c!r} in {vid} have {sorted(icodes)}")
    else:
        targets = [v for v in vals if str(v.get("validator_id") or "") == exp_val and str(v.get("status") or "") in ("fail", "crash")]
        if not targets:
            errs.append(f"{name}: allow_prior_fail: no failure for validator {exp_val}")
        else:
            icodes: set[str] = set()
            for t in targets:
                icodes |= _issue_codes_from_validator(t)
            for c in exp_codes:
                if c not in icodes:
                    errs.append(f"{name}: missing issue code {c!r} (allow_prior) have {sorted(icodes)}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-report", action="store_true", help="Emit one JSON summary line to stdout")
    ap.add_argument("--verbose", action="store_true", help="Print fixture name as each fixture is checked (I3)")
    args = ap.parse_args()
    py = sys.executable
    summary: dict[str, object] = {"fixtures": [], "ok": True}
    all_errs: list[str] = []
    for base, label in ((GOOD, "good"), (BAD, "bad")):
        if not base.is_dir():
            all_errs.append(f"missing {base}")
            continue
        for fixture_dir in sorted(base.iterdir()):
            if not fixture_dir.is_dir():
                continue
            name = f"{label}/{fixture_dir.name}"
            if args.verbose:
                print(f"[fixture] {name}", file=sys.stderr)
            fb = _forbidden_paths(fixture_dir)
            if fb:
                all_errs.append(f"{name}: FIXTURE-HYGIENE-VIOLATION forbidden files: {fb}")
                continue
            exp_path = fixture_dir / "expected.json"
            if not exp_path.is_file():
                all_errs.append(f"{name}: FIXTURE-MISSING-EXPECTED")
                continue
            try:
                exp = json.loads(exp_path.read_text(encoding="utf-8"))
            except Exception as e:
                all_errs.append(f"{name}: expected.json parse error {e}")
                continue
            if not isinstance(exp, dict):
                all_errs.append(f"{name}: expected.json not an object")
                continue
            profile = str(exp.get("expected_profile") or "mvr")
            rc, tr, raw = _run_one(fixture_dir, py, profile)
            errs = _check_expected(name, rc, tr, exp, raw)
            all_errs.extend(errs)
            summary["fixtures"].append({"name": name, "rc": rc, "errors": errs})
    summary["ok"] = not all_errs
    if args.json_report:
        print(json.dumps({"status": "pass" if not all_errs else "fail", "errors": all_errs, "summary": summary}, ensure_ascii=False))
    else:
        for e in all_errs:
            print(e, file=sys.stderr)
    return 0 if not all_errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
