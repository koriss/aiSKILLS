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
    opts = prof.get("options")
    if not isinstance(opts, dict):
        opts = {}
    used_profile = {
        "profile": args.profile,
        "schema_version": prof.get("schema_version"),
        "options": opts,
    }
    (rd / "validation-profile-used.json").write_text(json.dumps(used_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run = {}
    if (rd / "run.json").is_file():
        try:
            run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        except Exception:
            pass
    run_id = str(run.get("run_id") or rd.name)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable
    results: list[dict] = []
    prior_fail = False
    for vid, script in CHAIN:
        if vid not in active:
            continue
        if prior_fail:
            results.append(
                {
                    "validator_id": vid,
                    "passed": True,
                    "blocking": False,
                    "issues": [],
                    "warnings": [{"code": "skipped_due_to_prior_failure", "severity": "warning", "path": "", "detail": "", "artifact": ""}],
                    "summary": "skipped",
                }
            )
            continue
        if not script.is_file():
            results.append(
                {
                    "validator_id": vid,
                    "passed": False,
                    "blocking": True,
                    "issues": [{"code": "CRASH", "severity": "error", "path": str(script), "detail": "missing script", "artifact": ""}],
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
                "issues": [{"code": "CRASH", "severity": "error", "path": "", "detail": (p.stderr or "")[-800:], "artifact": ""}],
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
        results.append({k: obj[k] for k in ("validator_id", "passed", "blocking", "issues", "warnings", "summary")})
        if p.returncode != 0 or obj.get("blocking"):
            prior_fail = True
    overall = all(r.get("passed") for r in results) and not any(r.get("blocking") for r in results)
    transcript = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "profile_used": args.profile,
        "validators": results,
        "overall_pass": overall,
        "all_passed": overall,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    out = rd / "validation-transcript.json"
    fd, tmp = tempfile.mkstemp(prefix="vt-", dir=str(rd), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n")
        Path(tmp).replace(out)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    print(json.dumps({"status": "pass" if overall else "fail", "overall_pass": overall}, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
