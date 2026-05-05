#!/usr/bin/env python3
"""Meta-validator: V1–V6 fixture matrix + failure-corpus error-code coverage (v19.1)."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOOD = ROOT / "tests" / "fixtures" / "v19" / "good"
BAD = ROOT / "tests" / "fixtures" / "v19" / "bad"
INDEX = ROOT / "failure-corpus" / "index-v19.json"

CHAIN = [
    "validate_artifact_schema",
    "validate_traceability",
    "validate_source_quality",
    "validate_claim_status",
    "validate_final_answer",
    "validate_delivery_truth",
]


def _expected_validator(fixture_dir: Path) -> str:
    exp = fixture_dir / "expected.json"
    if not exp.is_file():
        return ""
    try:
        o = json.loads(exp.read_text(encoding="utf-8"))
        return str(o.get("expected_validator") or "") if isinstance(o, dict) else ""
    except Exception:
        return ""


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def _issue_codes_from_transcript(run_dir: Path) -> set[str]:
    p = run_dir / "validation-transcript.json"
    if not p.is_file():
        return set()
    try:
        tr = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out: set[str] = set()
    for v in tr.get("validators") or []:
        if not isinstance(v, dict):
            continue
        for it in v.get("issues") or []:
            if isinstance(it, dict) and it.get("code"):
                out.add(str(it["code"]))
        for w in v.get("warnings") or []:
            if isinstance(w, dict) and w.get("code"):
                out.add(str(w["code"]))
    return out


def _profile_for_fixture(fixture_dir: Path) -> str:
    exp = fixture_dir / "expected.json"
    if not exp.is_file():
        return "mvr"
    try:
        o = json.loads(exp.read_text(encoding="utf-8"))
        return str(o.get("expected_profile") or "mvr") if isinstance(o, dict) else "mvr"
    except Exception:
        return "mvr"


def _run_fixture_codes(py: str, fixture_dir: Path) -> set[str]:
    prof = _profile_for_fixture(fixture_dir)
    with tempfile.TemporaryDirectory(prefix="rfo-cov-") as td:
        rd = Path(td) / "run"
        _copy_fixture(fixture_dir, rd)
        subprocess.run(
            [py, "-S", str(ROOT / "scripts" / "run_core_validators.py"), "--run-dir", str(rd), "--profile", prof],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return _issue_codes_from_transcript(rd)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="", help="coverage-report.json path (default: ./coverage-report.json)")
    args = ap.parse_args()
    py = sys.executable

    gaps: list[str] = []
    bad_validators: set[str] = set()
    if not BAD.is_dir():
        gaps.append("missing bad fixtures root")
    else:
        for d in sorted(BAD.iterdir()):
            if not d.is_dir():
                continue
            ev = _expected_validator(d)
            if ev:
                bad_validators.add(ev)

    for vid in CHAIN:
        if vid not in bad_validators:
            gaps.append(f"no bad fixture declares expected_validator={vid!r}")

    good_ok = (GOOD / "mvr_minimal_valid").is_dir() and (GOOD / "mvr_minimal_valid" / "expected.json").is_file()
    if not good_ok:
        gaps.append("missing good/mvr_minimal_valid")

    idx_codes: list[dict[str, object]] = []
    if not INDEX.is_file():
        gaps.append("missing failure-corpus/index-v19.json")
    else:
        idx = json.loads(INDEX.read_text(encoding="utf-8"))
        idx_codes = [c for c in (idx.get("codes") or []) if isinstance(c, dict)]

    repro_cache: dict[str, set[str]] = {}

    def codes_for_repro(repro: str) -> set[str]:
        sub = repro.removeprefix("bad/").strip("/")
        if sub in repro_cache:
            return repro_cache[sub]
        fd = BAD / sub
        if not fd.is_dir():
            repro_cache[sub] = set()
            return repro_cache[sub]
        repro_cache[sub] = _run_fixture_codes(py, fd)
        return repro_cache[sub]

    for row in idx_codes:
        code = str(row.get("code") or "")
        sev = str(row.get("severity") or "").lower()
        repro = str(row.get("reproduces_in_fixture") or "").strip()
        if not code or sev != "error":
            continue
        if repro in ("n/a", "suite-level", ""):
            continue
        obs = codes_for_repro(repro)
        if code not in obs:
            gaps.append(f"corpus code {code!r} not observed in transcript for repro {repro!r} (have {sorted(obs)!r})")

    report: dict[str, object] = {
        "schema_version": "v19.1",
        "validators_with_bad_fixture": sorted(bad_validators),
        "good_fixture_ok": good_ok,
        "gaps": gaps,
        "failure_corpus_error_rows": len([c for c in idx_codes if str(c.get("severity") or "").lower() == "error"]),
    }
    out_path = Path(args.out) if args.out else ROOT / "coverage-report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if gaps:
        print(json.dumps({"error": "COVERAGE-GAP", "gaps": gaps, "report": str(out_path)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "report": str(out_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
