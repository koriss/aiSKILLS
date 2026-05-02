#!/usr/bin/env python3
"""Ensure release report claims match a fresh release-validation-transcript (optional markdown report path)."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sha256_obj(o: object) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True, help="Path to release-validation-transcript.json")
    ap.add_argument("report_path", nargs="?", default="", help="Optional release report .md or .json")
    args = ap.parse_args()
    tp = Path(args.transcript)
    if not tp.is_file():
        print(
            json.dumps(
                {"status": "fail", "reason": "missing transcript", "issue_code": "release_missing_transcript"},
                ensure_ascii=False,
            )
        )
        return 1
    fresh = json.loads(tp.read_text(encoding="utf-8"))
    fresh_sha = _sha256_obj({k: v for k, v in fresh.items() if k != "transcript_sha256"})
    if fresh.get("transcript_sha256") and fresh["transcript_sha256"] != fresh_sha:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "reason": "transcript self-hash mismatch (regenerate validate_release)",
                    "issue_code": "release_transcript_hash_mismatch",
                },
                ensure_ascii=False,
            )
        )
        return 1

    # F199-style: duplicate run_id across distinct smoke-derived dirs in transcript
    run_ids = []
    seen_rd = set()
    for step in fresh.get("steps") or []:
        rd = step.get("smoke_run_dir") or step.get("run_dir")
        if not rd or rd in seen_rd:
            continue
        if Path(rd).is_dir():
            seen_rd.add(rd)
            rj = Path(rd) / "run.json"
            if rj.is_file():
                run_ids.append(json.loads(rj.read_text(encoding="utf-8")).get("run_id"))
    if len(run_ids) >= 2 and len(set(run_ids)) < len(run_ids):
        print(
            json.dumps(
                {
                    "status": "fail",
                    "reason": "duplicate run_id across transcript run_dirs",
                    "run_ids": run_ids,
                    "issue_code": "release_duplicate_run_id",
                },
                ensure_ascii=False,
            )
        )
        return 1

    # Version consistency across embedded run_dirs vs runtime/version.json
    from runtime.status import VERSION as SKILL_VER

    vers = {SKILL_VER}
    seen2 = set()
    for step in fresh.get("steps") or []:
        rd = step.get("smoke_run_dir") or step.get("run_dir")
        if not rd or rd in seen2:
            continue
        if Path(rd).is_dir():
            seen2.add(rd)
            rj = Path(rd) / "run.json"
            if rj.is_file():
                vers.add(str(json.loads(rj.read_text(encoding="utf-8")).get("version") or ""))
    vers.discard("")
    if len(vers) > 1:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "reason": "run.json version mismatch across transcript",
                    "versions": sorted(vers),
                    "issue_code": "release_run_version_mismatch",
                },
                ensure_ascii=False,
            )
        )
        return 1

    def _ftm_stub_entries(run_dir: str) -> list[str]:
        fp = Path(run_dir) / "feature-truth-matrix.json"
        if not fp.is_file():
            return []
        try:
            ftm = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            return ["feature-truth-matrix.json:unparseable"]
        if not isinstance(ftm, dict):
            return []
        bad: list[str] = []
        feats = ftm.get("features") or {}
        for k, v in feats.items():
            if isinstance(v, dict):
                st = str(v.get("status", "")).lower()
            else:
                st = str(v).lower()
            if st in ("stub", "missing", "scaffold"):
                bad.append(f"{k}={st}")
        return bad

    ftm_issues: list[dict] = []
    seen_rd: set[str] = set()
    for step in fresh.get("steps") or []:
        rd = step.get("smoke_run_dir") or step.get("run_dir")
        if not rd or not isinstance(rd, str) or rd in seen_rd:
            continue
        if not Path(rd).is_dir():
            continue
        seen_rd.add(rd)
        stubs = _ftm_stub_entries(rd)
        if stubs:
            ftm_issues.append({"run_dir": rd, "stub_or_missing": stubs})

    rp = args.report_path.strip()
    if not rp or not Path(rp).is_file():
        print(json.dumps({"status": "pass", "note": "no release report provided; transcript integrity only"}, ensure_ascii=False))
        return 0

    text = Path(rp).read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    # FTM (v18.7): report must not claim production readiness while embedded smoke run_dir still has stub/missing FTM rows
    prod_pass_claim = bool(
        re.search(r"(production|prod)\s*(cycle|mode|run).{0,240}(pass|complete|green|ready|success)", low, re.DOTALL)
    ) or ("production" in low and re.search(r"(release|validation|smoke).{0,120}(pass|complete|green)", low, re.DOTALL))
    if prod_pass_claim and ftm_issues:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "reason": "feature_truth_matrix_stub_under_production_claim",
                    "ftm_issues": ftm_issues,
                    "issue_code": "release_ftm_stub_under_production_claim",
                },
                ensure_ascii=False,
            )
        )
        return 1

    passes = re.findall(r"(?m)^\s*([^:\n]+):\s*pass\s*$", text)
    step_names = {s.get("name") for s in (fresh.get("steps") or [])}
    for label in passes:
        lab = label.strip()
        if lab and lab not in step_names and "validate" in lab.lower():
            # allow loose matching: substring
            if not any(lab in n or n in lab for n in step_names if n):
                print(
                    json.dumps(
                        {
                            "status": "fail",
                            "reason": "report claims pass without matching transcript step",
                            "label": lab,
                            "issue_code": "release_pass_without_transcript",
                        },
                        ensure_ascii=False,
                    )
                )
                return 1

    print(json.dumps({"status": "pass", "report_checked": rp}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
