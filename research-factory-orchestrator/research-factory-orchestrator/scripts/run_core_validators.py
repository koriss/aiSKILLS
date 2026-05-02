#!/usr/bin/env python3
"""v19 — run V1..V6 sequentially, emit validation-transcript.json (atomic write)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CHAIN = [
    ("validate_artifact_schema", ROOT / "validators" / "core" / "validate_artifact_schema.py"),
    ("validate_traceability", ROOT / "validators" / "core" / "validate_traceability.py"),
    ("validate_source_quality", ROOT / "validators" / "core" / "validate_source_quality.py"),
    ("validate_claim_status", ROOT / "validators" / "core" / "validate_claim_status.py"),
    ("validate_final_answer", ROOT / "validators" / "core" / "validate_final_answer.py"),
    ("validate_delivery_truth", ROOT / "validators" / "core" / "validate_delivery_truth.py"),
]


class ValidatorStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    CRASH = "crash"


def _build_used_profile(profile_name: str, prof: dict[str, object]) -> dict[str, object]:
    opts = prof.get("options")
    if not isinstance(opts, dict):
        opts = {}
    ctp = prof.get("claim_type_policies")
    if not isinstance(ctp, dict):
        ctp = {}
    br = prof.get("blocking_rules")
    if not isinstance(br, dict):
        br = {}
    sp = prof.get("source_policy")
    if not isinstance(sp, dict):
        sp = {}
    dp = prof.get("delivery_policy")
    if not isinstance(dp, dict):
        dp = {}
    return {
        "schema_version": prof.get("schema_version"),
        "profile": profile_name,
        "profile_id": str(prof.get("profile_id") or profile_name),
        "profile_name": str(prof.get("profile_name") or prof.get("profile") or profile_name),
        "description": prof.get("description"),
        "parent_profile": prof.get("parent_profile"),
        "options": opts,
        "claim_type_policies": ctp,
        "blocking_rules": br,
        "source_policy": sp,
        "delivery_policy": dp,
        "auto_escalation": prof.get("auto_escalation") if isinstance(prof.get("auto_escalation"), dict) else {},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--profile", default="mvr", help="Profile name (without .json) under validation-profiles/")
    args = ap.parse_args()
    rd = Path(args.run_dir)
    if not rd.is_dir():
        print(json.dumps({"error": "bad_run_dir", "path": str(rd)}), file=sys.stderr)
        return 2
    prof_path = ROOT / "validation-profiles" / f"{args.profile}.json"
    if not prof_path.is_file():
        print(json.dumps({"error": "missing_profile", "path": str(prof_path)}), file=sys.stderr)
        return 2
    prof = json.loads(prof_path.read_text(encoding="utf-8"))
    active = prof.get("active_validators") or [x[0] for x in CHAIN]
    if not isinstance(active, list):
        active = [x[0] for x in CHAIN]
    used_profile = _build_used_profile(args.profile, prof)
    (rd / "validation-profile-used.json").write_text(
        json.dumps(used_profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    run: dict[str, object] = {}
    if (rd / "run.json").is_file():
        try:
            run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        except Exception:
            run = {}
    run_id = str(run.get("run_id") or rd.name)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable
    results: list[dict[str, object]] = []
    prior_fail = False
    for vid, script in CHAIN:
        if vid not in active:
            continue
        if prior_fail:
            results.append(
                {
                    "validator_id": vid,
                    "status": ValidatorStatus.SKIPPED.value,
                    "passed": False,
                    "blocking": False,
                    "issues": [],
                    "warnings": [
                        {
                            "code": "skipped_due_to_prior_failure",
                            "severity": "warning",
                            "path": "",
                            "detail": "",
                            "artifact": "",
                        }
                    ],
                    "summary": "skipped",
                }
            )
            continue
        if not script.is_file():
            results.append(
                {
                    "validator_id": vid,
                    "status": ValidatorStatus.CRASH.value,
                    "passed": False,
                    "blocking": True,
                    "issues": [
                        {
                            "code": "CRASH",
                            "severity": "error",
                            "path": str(script),
                            "detail": "missing script",
                            "artifact": "",
                        }
                    ],
                    "warnings": [],
                    "summary": "missing validator script",
                }
            )
            prior_fail = True
            continue
        p = subprocess.run(
            [py, "-S", str(script), "--run-dir", str(rd)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        raw = (p.stdout or "").strip()
        try:
            obj = json.loads(raw.splitlines()[-1] if raw else "{}")
        except Exception:
            obj = {
                "validator_id": vid,
                "schema_version": "v19.0",
                "passed": False,
                "blocking": True,
                "issues": [
                    {
                        "code": "CRASH",
                        "severity": "error",
                        "path": "",
                        "detail": (p.stderr or "")[-800:],
                        "artifact": "",
                    }
                ],
                "warnings": [],
                "summary": "non-json stdout",
            }
        if not isinstance(obj, dict):
            obj = {"validator_id": vid, "passed": False, "blocking": True, "issues": [{"code": "CRASH"}], "warnings": [], "summary": "bad shape"}
        obj.setdefault("validator_id", vid)
        obj.setdefault("passed", p.returncode == 0)
        obj.setdefault("blocking", not obj.get("passed"))
        obj.setdefault("issues", [])
        obj.setdefault("warnings", [])
        obj.setdefault("summary", "")
        passed_ok = p.returncode == 0 and bool(obj.get("passed")) and not bool(obj.get("blocking"))
        if passed_ok:
            st = ValidatorStatus.PASS.value
        elif isinstance(obj, dict) and (obj.get("issues") or obj.get("summary") or obj.get("validator_id") == vid):
            st = ValidatorStatus.FAIL.value
        else:
            st = ValidatorStatus.CRASH.value
        row = {
            "validator_id": vid,
            "status": st,
            "passed": passed_ok,
            "blocking": bool(obj.get("blocking")),
            "issues": obj.get("issues") or [],
            "warnings": obj.get("warnings") or [],
            "summary": str(obj.get("summary") or ""),
        }
        results.append(row)
        if not passed_ok or st == ValidatorStatus.CRASH.value:
            prior_fail = True
    statuses = [str(r.get("status") or "") for r in results]
    all_pass = all(s == ValidatorStatus.PASS.value for s in statuses) and bool(results)
    top = ValidatorStatus.PASS.value if all_pass else ValidatorStatus.FAIL.value
    transcript: dict[str, object] = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "profile_used": args.profile,
        "status": top,
        "validators": results,
        "overall_pass": all_pass,
        "all_passed": all_pass,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    out = rd / "validation-transcript.json"
    fd, tmp = tempfile.mkstemp(prefix="vt-", dir=str(rd), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(transcript, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        Path(tmp).replace(out)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print(
        json.dumps(
            {"status": top, "overall_pass": all_pass},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
