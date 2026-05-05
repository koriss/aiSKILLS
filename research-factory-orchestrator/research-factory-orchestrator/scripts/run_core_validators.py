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


def _ts_iso() -> str:
    return os.environ.get("RFO_FIXED_TIME", "").strip() or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_run_event(rd: Path, event: str, fields: dict[str, object]) -> None:
    ts = _ts_iso()
    row: dict[str, object] = {"event": event, "timestamp": ts}
    row.update(fields)
    p = rd / "run-events.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def _advisory_judge_council(rd: Path) -> dict[str, object] | None:
    """Optional judge-council.json (v19.1); heuristic consensus check, advisory only."""
    p = rd / "judge-council.json"
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"present": True, "status": "parse_error", "detail": str(e)[:400]}
    if not isinstance(raw, dict):
        return {"present": True, "status": "bad_shape"}
    judges = raw.get("judges")
    cons = raw.get("consensus")
    if not isinstance(judges, list) or not isinstance(cons, dict):
        return {"present": True, "status": "bad_shape"}
    verdicts = [str(j.get("verdict") or "") for j in judges if isinstance(j, dict)]
    method = str(cons.get("method") or "")
    declared = cons.get("reached")
    non_abs = [v for v in verdicts if v in ("pass", "fail")]
    passes = sum(1 for v in non_abs if v == "pass")
    fails = sum(1 for v in non_abs if v == "fail")
    n = len(non_abs)
    computed = False
    if method == "unanimous":
        computed = n > 0 and fails == 0 and passes == n
    elif method == "majority":
        computed = n > 0 and passes > fails
    elif method == "weighted":
        wmap = cons.get("weights") if isinstance(cons.get("weights"), dict) else {}
        score = 0.0
        tw = 0.0
        for j in judges:
            if not isinstance(j, dict):
                continue
            jid = str(j.get("id") or "")
            w = float(wmap.get(jid, 1.0)) if isinstance(wmap.get(jid), (int, float)) else 1.0
            v = str(j.get("verdict") or "")
            if v == "pass":
                score += w
            elif v == "fail":
                score -= w
            tw += abs(w)
        computed = tw > 0 and score > 0
    else:
        computed = bool(declared)
    align = "match" if isinstance(declared, bool) and declared == computed else ("mismatch" if isinstance(declared, bool) else "unknown")
    return {
        "present": True,
        "status": "ok",
        "method": method,
        "declared_reached": declared,
        "computed_reached": computed,
        "alignment": align,
    }


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
    evp = rd / "run-events.jsonl"
    try:
        if evp.exists():
            evp.unlink()
    except OSError:
        pass
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable
    results: list[dict[str, object]] = []
    prior_fail = False
    for vid, script in CHAIN:
        if vid not in active:
            continue
        _append_run_event(
            rd,
            "validator.started",
            {"validator_id": vid, "blocking_expected": vid in active},
        )
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
            _append_run_event(
                rd,
                "validator.finished",
                {"validator_id": vid, "passed": False, "blocking": False, "status": ValidatorStatus.SKIPPED.value},
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
            _append_run_event(
                rd,
                "validator.finished",
                {"validator_id": vid, "passed": False, "blocking": True, "status": "crash"},
            )
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
        _append_run_event(
            rd,
            "validator.finished",
            {
                "validator_id": vid,
                "passed": passed_ok,
                "blocking": bool(row.get("blocking")),
                "status": st,
            },
        )
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
        "created_at": _ts_iso(),
    }
    # Advisory channel: blinded checker (MARCH-style); never changes blocking / overall_pass.
    adv: dict[str, object] = {}
    blind_script = ROOT / "scripts" / "run_blinded_checker.py"
    if blind_script.is_file():
        bp = subprocess.run(
            [py, "-S", str(blind_script), "--run-dir", str(rd)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        brp = rd / "validation" / "blinded-checker-report.json"
        rep: dict[str, object] = {}
        if brp.is_file():
            try:
                rep = json.loads(brp.read_text(encoding="utf-8"))
                if not isinstance(rep, dict):
                    rep = {}
            except Exception:
                rep = {"error": "bad_json", "path": str(brp)}
        if bp.returncode != 0:
            rep = {**rep, "runner_error": (bp.stderr or "")[-800:]}
        adv["blinded_checker"] = {
            "status": "ok" if rep.get("overall_match") is True else ("mismatch" if rep.get("overall_match") is False else "unknown"),
            "mismatch_claim_ids": rep.get("mismatch_claim_ids") if isinstance(rep.get("mismatch_claim_ids"), list) else [],
            "report_path": str(brp) if brp.is_file() else "",
        }
    tg_script = ROOT / "scripts" / "run_typed_grounding.py"
    if tg_script.is_file():
        tp = subprocess.run(
            [py, "-S", str(tg_script), "--run-dir", str(rd)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        tgr = rd / "validation" / "typed-grounding-report.json"
        tgo: dict[str, object] = {}
        if tgr.is_file():
            try:
                tgo = json.loads(tgr.read_text(encoding="utf-8"))
                if not isinstance(tgo, dict):
                    tgo = {}
            except Exception:
                tgo = {"error": "bad_json", "path": str(tgr)}
        if tp.returncode != 0:
            tgo = {**tgo, "runner_error": (tp.stderr or "")[-800:]}
        infl = tgo.get("typed_groundedness_inflation") if isinstance(tgo.get("typed_groundedness_inflation"), list) else []
        adv["typed_grounding"] = {
            "S": tgo.get("S"),
            "decision_advisory": tgo.get("decision_advisory"),
            "status": "inflation" if infl else "ok",
            "typed_groundedness_inflation": infl,
            "report_path": str(tgr) if tgr.is_file() else "",
        }
    jc = _advisory_judge_council(rd)
    if jc:
        adv["judge_council"] = jc
    spg = ROOT / "scripts" / "build_sacred_path_graph.py"
    if spg.is_file():
        subprocess.run(
            [py, "-S", str(spg), "--run-dir", str(rd)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    if adv:
        transcript["advisory_channels"] = adv
    out = rd / "validation-transcript.json"
    fd, tmp = tempfile.mkstemp(prefix="vt-", dir=str(rd), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(transcript, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        Path(tmp).replace(out)
        _append_run_event(
            rd,
            "artifact.written",
            {"path": "validation-transcript.json", "kind": "validation_transcript"},
        )
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
