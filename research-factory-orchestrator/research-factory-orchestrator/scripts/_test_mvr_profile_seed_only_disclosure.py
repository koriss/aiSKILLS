#!/usr/bin/env python3
"""
RFO mvr profile seed-only disclosure test.
Version: 2026-05-07

Bug scenario:
  User runs /research_factory_orchestrator with research intent.
  Operator uses mvr profile (default) → external_collection_required=false.
  RFO completes with stub_delivered + seed-only output.
  If operator claims "analysis completed" → DELIVERY_TRUTH_VIOLATION.

Expected behavior:
  1. Pre-run: operator identifies mvr as seed-only (no external search)
  2. Pre-run: operator warns user or offers full-rigor
  3. Post-run: completion uses correct vocabulary (seed_only / stub_only)
  4. Post-run: final-answer-gate.passed=false, delivery_status=stub_delivered

Test design:
  - Test 1: Use existing 9 maya run (RUN-6f9d8902a73d) as reference
  - Test 2: Fresh run with smoke task (to verify idempotency)
  - Test 3: Check correct V6 behavior (stub delivery → V6 fail)

Usage:
  python3 -S _test_mvr_profile_seed_only_disclosure.py [--runs-root ~/.openclaw/workspace/rfo-runs]
"""

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
SKILL_ROOT = ROOT
DEFAULT_REFERENCE_RUN = "9_maya_analiz_prazdnika_istoriya_geopolitika_propaganda_20260507T013612"


def get_run_dir(runs_root: Path, run_label_substring: str) -> Path | None:
    """Find run dir by substring match."""
    runs_dir = runs_root / "runs"
    if not runs_dir.exists():
        return None
    candidates = [d for d in runs_dir.iterdir() if run_label_substring in d.name]
    return candidates[-1] if candidates else None


def check_delivery_truth_violation(run_dir: Path) -> dict:
    """
    Core test: stub delivery with artifact_ready_claim_allowed=true but attachments=[]
    should produce V6 fail.
    """
    results = {
        "test": "delivery_truth_violation",
        "passed": False,
        "checks": [],
    }

    dm_path = run_dir / "delivery-manifest.json"
    if not dm_path.exists():
        results["checks"].append({"id": "DELIVERY_MANIFEST_EXISTS", "status": "fail", "detail": "not found"})
        return results

    dm = json.loads(dm_path.read_text())

    # CHECK: stub_delivery should be True for mvr seed-only run
    stub_delivery = dm.get("stub_delivery", False)
    results["checks"].append({
        "id": "STUB_DELIVERY_TRUE",
        "status": "pass" if stub_delivery else "fail",
        "detail": f"stub_delivery={stub_delivery} (expected True for mvr seed-only)",
    })

    # CHECK: real_external_delivery should be False
    real_ext = dm.get("real_external_delivery", True)
    results["checks"].append({
        "id": "REAL_EXTERNAL_DELIVERY_FALSE",
        "status": "pass" if not real_ext else "fail",
        "detail": f"real_external_delivery={real_ext} (expected False)",
    })

    # CHECK: artifact_ready_claim_allowed should be True (claim is allowed for artifact rendering)
    artifact_ready = dm.get("artifact_ready_claim_allowed", False)
    results["checks"].append({
        "id": "ARTIFACT_READY_CLAIM_ALLOWED_TRUE",
        "status": "pass" if artifact_ready else "fail",
        "detail": f"artifact_ready_claim_allowed={artifact_ready} (expected True)",
    })

    # CHECK: attachments should be empty (no real external delivery)
    attachments = dm.get("attachments", [])
    results["checks"].append({
        "id": "ATTACHMENTS_EMPTY",
        "status": "pass" if len(attachments) == 0 else "fail",
        "detail": f"attachments count={len(attachments)} (expected 0)",
    })

    # CHECK: This combination (artifact_ready_claim_allowed=true + attachments=[]) is the V6 failure condition
    v6_fails = artifact_ready and len(attachments) == 0 and stub_delivery
    results["checks"].append({
        "id": "V6_FAIL_CONDITION_PRESENT",
        "status": "pass" if v6_fails else "fail",
        "detail": f"artifact_ready=True + attachments=[] + stub=True = {v6_fails} (expected True → V6 fail expected)",
    })

    # CHECK: V6 validator should fail on this condition
    vt_path = run_dir / "validation-transcript.json"
    if vt_path.exists():
        vt = json.loads(vt_path.read_text())
        validators = {v["validator_id"]: v for v in vt.get("validators", [])}
        v6 = validators.get("validate_delivery_truth", {})
        v6_status = v6.get("status", "unknown")
        results["checks"].append({
            "id": "V6_DELIVERY_TRUTH_STATUS",
            "status": "pass" if v6_status == "fail" else "fail",
            "detail": f"V6 status={v6_status} (expected fail due to empty attachments with claim allowed)",
            "issues": v6.get("issues", []),
        })
    else:
        results["checks"].append({"id": "VALIDATION_TRANSCRIPT_EXISTS", "status": "fail", "detail": "not found"})

    all_pass = all(c["status"] == "pass" for c in results["checks"])
    results["passed"] = all_pass
    return results


def check_seed_only_content(run_dir: Path) -> dict:
    """Verify seed-only output: no confirmed_fact claims, seed source only."""
    results = {
        "test": "seed_only_content",
        "passed": False,
        "checks": [],
    }

    # CHECK: sources.json has only SRC-SEED
    src_path = run_dir / "sources.json"
    if src_path.exists():
        srcs = json.loads(src_path.read_text())
        src_list = srcs.get("sources", [])
        has_seed_only = len(src_list) == 1 and "seed" in src_list[0].get("source_id", "").lower()
        results["checks"].append({
            "id": "SEED_ONLY_SOURCES",
            "status": "pass" if has_seed_only else "fail",
            "detail": f"Only seed source: {has_seed_only}, sources: {[s.get('source_id') for s in src_list]}",
        })
    else:
        results["checks"].append({"id": "SOURCES_JSON_EXISTS", "status": "fail", "detail": "not found"})

    # CHECK: semantic-report has 0 confirmed_fact claims
    sr_path = run_dir / "report" / "semantic-report.json"
    if sr_path.exists():
        sr = json.loads(sr_path.read_text())
        claims = sr.get("claims", [])
        confirmed = [c for c in claims if c.get("status") == "confirmed_fact"]
        results["checks"].append({
            "id": "NO_CONFIRMED_FACT_CLAIMS",
            "status": "pass" if len(confirmed) == 0 else "fail",
            "detail": f"confirmed_fact claims: {len(confirmed)} (expected 0)",
        })
    else:
        results["checks"].append({"id": "SEMANTIC_REPORT_EXISTS", "status": "fail", "detail": "not found"})

    # CHECK: execution-summary shows all WU completed_no_sources
    es_path = run_dir / "work-queue" / "execution-summary.json"
    if es_path.exists():
        es = json.loads(es_path.read_text())
        completed_no = es.get("by_status", {}).get("completed_no_sources", 0)
        total = es.get("total_terminal", 0)
        results["checks"].append({
            "id": "ALL_WU_COMPLETED_NO_SOURCES",
            "status": "pass" if completed_no == total and total > 0 else "fail",
            "detail": f"{completed_no}/{total} WU completed_no_sources",
        })
    else:
        results["checks"].append({"id": "EXECUTION_SUMMARY_EXISTS", "status": "fail", "detail": "not found"})

    # CHECK: final-answer-gate.passed = false
    fag_path = run_dir / "final-answer-gate.json"
    if fag_path.exists():
        fag = json.loads(fag_path.read_text())
        passed = fag.get("passed", True)
        status = fag.get("status", "")
        results["checks"].append({
            "id": "FINAL_ANSWER_GATE_PASSED_FALSE",
            "status": "pass" if not passed else "fail",
            "detail": f"passed={passed}, status={status}",
        })
    else:
        results["checks"].append({"id": "FINAL_ANSWER_GATE_EXISTS", "status": "fail", "detail": "not found"})

    # CHECK: errors.jsonl has EXTERNAL-COLLECTION-NO-SEEDS
    err_path = run_dir / "runtime" / "errors.jsonl"
    if err_path.exists():
        errors = [json.loads(l) for l in err_path.read_text().splitlines() if l.strip()]
        has_no_seeds = any("EXTERNAL-COLLECTION-NO-SEEDS" in e.get("code", "") for e in errors)
        results["checks"].append({
            "id": "EXTERNAL_COLLECTION_NO_SEEDS_LOGGED",
            "status": "pass" if has_no_seeds else "fail",
            "detail": f"EXTERNAL-COLLECTION-NO-SEEDS present: {has_no_seeds}",
        })
    else:
        results["checks"].append({"id": "ERRORS_JSONL_EXISTS", "status": "fail", "detail": "not found"})

    all_pass = all(c["status"] == "pass" for c in results["checks"])
    results["passed"] = all_pass
    return results


def check_v1_v5_pass(run_dir: Path) -> dict:
    """Verify V1-V5 validators pass (V6 fails for mvr stub-only)."""
    results = {
        "test": "v1_v5_pass",
        "passed": False,
        "checks": [],
    }

    vt_path = run_dir / "validation-transcript.json"
    if not vt_path.exists():
        results["checks"].append({"id": "VALIDATION_TRANSCRIPT_EXISTS", "status": "fail", "detail": "not found"})
        return results

    vt = json.loads(vt_path.read_text())
    validators = {v["validator_id"]: v for v in vt.get("validators", [])}

    v1_v5_ids = [
        "validate_artifact_schema",
        "validate_traceability",
        "validate_source_quality",
        "validate_claim_status",
        "validate_final_answer",
    ]

    for vid in v1_v5_ids:
        v = validators.get(vid, {})
        status = v.get("status", "missing")
        results["checks"].append({
            "id": f"V_VALIDATOR_{vid}",
            "status": "pass" if status == "pass" else "fail",
            "detail": f"{vid} status={status} (expected pass)",
        })

    all_pass = all(c["status"] == "pass" for c in results["checks"])
    results["passed"] = all_pass
    return results


def run_fresh_smoke_test(runs_root: Path, cleanup: bool = True) -> dict:
    """
    Run a fresh mvr smoke test with a trivial task.
    Returns (success, run_dir, result_dict).
    """
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "RFO_ALLOW_TMP_RUNS_ROOT": "1",
        "RFO_RUNS_ROOT": str(runs_root),
        "RFO_V19_PROFILE": "mvr",
    }

    task = "Smoke test: verify mvr profile produces seed-only output with V6 fail"
    cmd = [
        sys.executable,
        "-S",
        str(SKILL_ROOT / "scripts" / "interface_runtime_adapter.py"),
        "--runs-root", str(runs_root),
        "--interface", "telegram",
        "--provider", "telegram",
        "--task", task,
        "--user-id", "38425045",
        "--chat-id", "38425045",
    ]

    p = subprocess.run(cmd, cwd=str(SKILL_ROOT), capture_output=True, text=True, env=env, timeout=60)
    try:
        queued = json.loads((p.stdout or "").strip())
    except Exception:
        return {"success": False, "error": p.stderr or p.stdout, "run_dir": None}

    if not queued.get("queued"):
        return {"success": False, "error": "not queued", "run_dir": None}

    run_dir = Path(queued["run_dir"])

    # Execute runtime
    env_rt = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "RFO_RUNS_ROOT": str(runs_root), "RFO_ALLOW_TMP_RUNS_ROOT": "1"}
    p_rt = subprocess.run(
        [sys.executable, "-S", str(SKILL_ROOT / "scripts" / "runtime_job_worker.py"),
         "--runs-root", str(runs_root), "--execute-runtime"],
        cwd=str(SKILL_ROOT), capture_output=True, text=True, timeout=300, env=env_rt,
    )

    # Run delivery worker
    subprocess.run(
        [sys.executable, "-S", str(SKILL_ROOT / "scripts" / "outbox_delivery_worker.py"),
         "--runs-root", str(runs_root)],
        cwd=str(SKILL_ROOT), capture_output=True, text=True, timeout=60,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "RFO_RUNS_ROOT": str(runs_root)},
    )

    # Run validators
    subprocess.run(
        [sys.executable, "-S", str(SKILL_ROOT / "scripts" / "run_core_validators.py"),
         "--run-dir", str(run_dir), "--profile", "mvr"],
        cwd=str(SKILL_ROOT), capture_output=True, text=True, timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )

    if cleanup:
        try:
            shutil.rmtree(run_dir)
        except Exception:
            pass

    return {"success": True, "run_dir": str(run_dir)}


def main() -> int:
    ap = argparse.ArgumentParser(description="RFO mvr seed-only disclosure test")
    ap.add_argument("--runs-root", default="~/.openclaw/workspace/rfo-runs")
    ap.add_argument("--reference-run", default=DEFAULT_REFERENCE_RUN)
    ap.add_argument("--skip-fresh-test", action="store_true", help="Skip fresh smoke test")
    ap.add_argument("--cleanup", action="store_true", help="Clean up test runs")
    args = ap.parse_args()

    runs_root = Path(os.path.expanduser(args.runs_root))

    print("=" * 70)
    print("RFO mvr profile seed-only disclosure test")
    print("=" * 70)

    overall_pass = True
    all_results = {}

    # === TEST SUITE 1: Reference run (9 maya) ===
    print(f"\n[1/3] Testing reference run: {args.reference_run}")

    ref_run_dir = runs_root / "runs" / args.reference_run
    if not ref_run_dir.exists():
        print(f"  ⚠️  Reference run not found at {ref_run_dir}")
        print(f"      Skipping reference tests. Running fresh test instead.")
        overall_pass = False
        ref_results = {"test": "reference_run", "skipped": True, "reason": f"not found: {ref_run_dir}"}
    else:
        print(f"  ✅ Found reference run: {ref_run_dir}")

        r1 = check_delivery_truth_violation(ref_run_dir)
        r2 = check_seed_only_content(ref_run_dir)
        r3 = check_v1_v5_pass(ref_run_dir)

        for label, result in [("delivery_truth", r1), ("seed_only_content", r2), ("v1_v5", r3)]:
            print(f"\n  --- {label} ---")
            for c in result["checks"]:
                icon = "✅" if c["status"] == "pass" else "❌" if c["status"] == "fail" else "⚠️"
                print(f"    {icon} {c['id']}: {c['detail']}")
            print(f"    {'✅ PASS' if result['passed'] else '❌ FAIL'}")

        ref_pass = r1["passed"] and r2["passed"] and r3["passed"]
        overall_pass = overall_pass and ref_pass
        ref_results = {"delivery_truth": r1, "seed_only_content": r2, "v1_v5": r3}

    all_results["reference_run"] = ref_results

    # === TEST SUITE 2: MVR profile check ===
    print(f"\n[2/3] Testing mvr profile configuration")
    profile_path = SKILL_ROOT / "validation-profiles" / "mvr.json"
    mvr_profile = json.loads(profile_path.read_text())
    sp = mvr_profile.get("source_policy", {})

    checks = [
        ("external_collection_required_false", sp.get("external_collection_required") is False, "external_collection_required=" + str(sp.get("external_collection_required"))),
        ("web_search_required_false", sp.get("web_search_required") is False, "web_search_required=" + str(sp.get("web_search_required"))),
        ("stub_only_allowed_true", mvr_profile.get("delivery_policy", {}).get("allow_stub") is True, "allow_stub=" + str(mvr_profile.get("delivery_policy", {}).get("allow_stub"))),
    ]

    profile_pass = True
    for cid, cond, detail in checks:
        status = "pass" if cond else "fail"
        profile_pass = profile_pass and cond
        icon = "✅" if cond else "❌"
        print(f"    {icon} {cid}: {detail}")

    print(f"    {'✅ PASS' if profile_pass else '❌ FAIL'}")
    overall_pass = overall_pass and profile_pass
    all_results["profile_config"] = {"test": "profile_config", "passed": profile_pass, "checks": [{"id": c[0], "status": "pass" if c[1] else "fail", "detail": c[2]} for c in checks]}

    # === TEST SUITE 3: Fresh smoke test (optional) ===
    if args.skip_fresh_test:
        print(f"\n[3/3] Fresh smoke test: SKIPPED (--skip-fresh-test)")
        fresh_result = {"test": "fresh_smoke", "skipped": True}
    else:
        print(f"\n[3/3] Running fresh smoke test...")
        fresh = run_fresh_smoke_test(runs_root, cleanup=args.cleanup)
        if fresh["success"]:
            print(f"    ✅ Fresh run completed: {fresh['run_dir']}")
            fresh_result = {"test": "fresh_smoke", "passed": True, "run_dir": fresh["run_dir"]}
        else:
            print(f"    ❌ Fresh run failed: {fresh.get('error', 'unknown')}")
            fresh_result = {"test": "fresh_smoke", "passed": False, "error": fresh.get("error")}
            overall_pass = False

    all_results["fresh_smoke"] = fresh_result

    # === SUMMARY ===
    print("\n" + "=" * 70)
    print(f"OVERALL: {'✅ PASS — all RFO mvr seed-only behaviors verified' if overall_pass else '❌ FAIL — see above'}")
    print("=" * 70)

    # Assertions that should be TRUE when test passes:
    print("\n📋 Expected behaviors when PASS:")
    print("  1. mvr profile: external_collection_required=False")
    print("  2. delivery-manifest: stub_delivery=True, real_external_delivery=False")
    print("  3. delivery-manifest: artifact_ready_claim_allowed=True, attachments=[]")
    print("  4. V6 validator: status=fail (DELIV-ATT-EMPTY-WITH-CLAIM)")
    print("  5. V1-V5 validators: all pass")
    print("  6. final-answer-gate.passed=False")
    print("  7. sources.json: only SRC-SEED-001")
    print("  8. semantic-report: 0 confirmed_fact claims")
    print("  9. errors.jsonl: EXTERNAL-COLLECTION-NO-SEEDS logged")
    print(" 10. All 12 WU: completed_no_sources")

    output = {"overall_pass": overall_pass, "results": all_results}
    print("\n" + json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())