"""Failure corpus coverage report (required F-classes + legacy bad-sample harness)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from runtime.status import VERSION
from runtime.util import jr, now, skill_root, tw


def cmd_failure(a):
    root = skill_root()
    idxp = root / "failure-corpus" / "index.json"
    idx = jr(idxp)
    if not idx:
        raise SystemExit("missing failure-corpus/index.json")
    required = set(x for x in (idx.get("required_failure_classes") or []) if isinstance(x, str))
    covered = set()

    def walk(o):
        if isinstance(o, dict):
            for c in o.get("covers") or []:
                if isinstance(c, str) and c.startswith("F"):
                    covered.add(c)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)

    walk(idx)
    for s in idx.get("v18_3_1_context_integrity_cases") or []:
        if isinstance(s, str):
            m = re.search(r"(F\d{3})", s)
            if m:
                covered.add(m.group(1))
    for s in idx.get("v18_3_2_delivery_truth_cases") or []:
        if isinstance(s, str) and s.startswith("F"):
            covered.add(s)
    for s in idx.get("v18_5_1_truth_gate_regression_cases") or []:
        if isinstance(s, str):
            m = re.search(r"(F\d{3})", s)
            if m:
                covered.add(m.group(1))
    missing = sorted(required - covered)
    scripts_dir = root / "scripts"
    cases_dir = root / "failure-corpus" / "cases"
    scenarios = []
    bad_runs = []
    for case in idx.get("legacy_v17_cases") or []:
        if not isinstance(case, dict):
            continue
        val, bad = case.get("validator"), case.get("bad_sample")
        if not val or not bad:
            continue
        sp, bp = scripts_dir / val, cases_dir / bad
        if not bp.exists():
            bp = root / "failure-corpus" / bad
        if not sp.is_file():
            scenarios.append({"case_id": case.get("case_id"), "skipped": True, "reason": "missing script or sample", "validator": val, "bad_sample": bad})
            continue
        if not bp.exists():
            scenarios.append({"case_id": case.get("case_id"), "skipped": True, "reason": "missing bad_sample path", "validator": val, "bad_sample": bad})
            continue
        exp = case.get("expected_bad", "fail")
        target = str(bp)
        p = subprocess.run([sys.executable, "-S", str(sp), target], capture_output=True, text=True, cwd=str(root), timeout=120)
        ok_bad = (p.returncode != 0) if exp in ("fail", "fail_or_gate_block") else (p.returncode == 0)
        row = {"case_id": case.get("case_id"), "validator": val, "bad_sample": target, "returncode": p.returncode, "expected": exp, "ok": ok_bad}
        scenarios.append(row)
        if not ok_bad:
            bad_runs.append(row)
    for case in idx.get("v18_7_logical_consistency_cases") or []:
        if not isinstance(case, dict):
            continue
        val = case.get("validator") or "validate_logical_consistency.py"
        bad = case.get("bad_sample") or ""
        if not bad:
            continue
        sp = scripts_dir / val if not str(val).startswith("/") else Path(val)
        bp = cases_dir / bad if not Path(bad).is_absolute() else Path(bad)
        if not sp.is_file():
            scenarios.append({"case_id": case.get("case_id"), "skipped": True, "reason": "missing logical consistency script", "validator": val})
            continue
        if not bp.is_dir():
            scenarios.append({"case_id": case.get("case_id"), "skipped": True, "reason": "missing v18.7 bad run_dir", "bad_sample": str(bp)})
            continue
        exp = case.get("expected_bad", "fail")
        p = subprocess.run([sys.executable, "-S", str(sp), str(bp)], capture_output=True, text=True, cwd=str(root), timeout=120)
        ok_bad = (p.returncode != 0) if exp in ("fail", "fail_or_gate_block") else (p.returncode == 0)
        row = {
            "case_id": case.get("case_id"),
            "validator": str(sp),
            "bad_sample": str(bp),
            "returncode": p.returncode,
            "expected": exp,
            "ok": ok_bad,
            "harness": "v18_7_logical_consistency",
        }
        scenarios.append(row)
        if not ok_bad:
            bad_runs.append(row)
    if bad_runs:
        pmd = root / "failure-corpus" / "postmortems"
        pmd.mkdir(parents=True, exist_ok=True)
        pm = pmd / "PM-failure-harness-stub.md"
        tw(pm, "# Postmortem stub (auto-generated)\n\n" + json.dumps(bad_runs[:12], ensure_ascii=False, indent=2) + "\n")
    ok = not missing and not bad_runs
    out = {
        "status": "pass" if ok else "fail",
        "version": VERSION,
        "required_failure_classes_total": len(required),
        "covered_failure_classes_total": len(covered & required),
        "coverage_missing": missing,
        "legacy_bad_sample_runs": scenarios,
        "bad_sample_mismatches": bad_runs,
        "generated_at": now(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 1
