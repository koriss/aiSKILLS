#!/usr/bin/env python3
"""Guard: every planned WU must reach a terminal status with matching evidence + events.

Closes failure code WORK-UNIT-NOT-EXECUTED. Refuses to PASS when:
  * work-unit-ledger.json plans WUs that were never moved past ``planned``;
  * any terminal WU lacks per-WU evidence file under ``work-queue/evidence/``;
  * observability-events.jsonl is missing matching ``work_unit_started`` /
    ``work_unit_completed`` pairs;
  * execution-summary.json reports ``total_terminal`` != ``total_planned``;
  * any WU claims ``status="completed"`` without ``sources_collected>0`` (must be
    ``completed_no_sources`` instead — honest seed-only marker).

stdlib-only, fail-closed; emits validator JSON envelope on stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


VALIDATOR_ID = "validate_work_unit_completion"


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": VALIDATOR_ID,
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": blocking,
                "issues": issues,
                "warnings": warnings,
                "summary": summary,
            },
            ensure_ascii=False,
        )
    )


def _load(p: Path):
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_parse_error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    ledger = _load(rd / "work-queue" / "work-unit-ledger.json")
    summary = _load(rd / "work-queue" / "execution-summary.json")
    events_path = rd / "observability-events.jsonl"
    if not isinstance(ledger, dict) or "_parse_error" in ledger:
        issues.append({"code": "WU-LEDGER-MISSING", "severity": "error", "detail": "work-unit-ledger.json missing or unreadable"})
        _emit(False, True, issues, warnings, "ledger missing")
        return 1
    wus = ledger.get("work_units") or []
    if not wus:
        warnings.append({"code": "WU-LEDGER-EMPTY", "severity": "warning", "detail": "no work units planned"})
    started: set[str] = set()
    completed: set[str] = set()
    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            name = ev.get("event_name")
            wu_id = ev.get("wu_id")
            if not isinstance(wu_id, str):
                continue
            if name == "work_unit_started":
                started.add(wu_id)
            elif name == "work_unit_completed":
                completed.add(wu_id)
    planned_ids = {wu.get("wu_id") for wu in wus if wu.get("wu_id")}
    for wu in wus:
        wu_id = wu.get("wu_id") or "<unknown>"
        status = wu.get("status")
        # Mirror runtime.work_units.WUStatus.TERMINAL exactly. Hardcoded here so the
        # validator stays stdlib-only and can be invoked from a stripped install.
        if status not in {"completed", "completed_no_sources", "failed", "skipped"}:
            issues.append({"code": "WORK-UNIT-NOT-EXECUTED", "severity": "error", "wu_id": wu_id, "detail": f"WU stuck at status={status!r}"})
            continue
        if status not in {"planned", "in_progress", "completed", "completed_no_sources", "failed", "skipped"}:
            issues.append({"code": "WU-UNKNOWN-STATUS", "severity": "error", "wu_id": wu_id, "detail": f"status={status!r} is not in WUStatus.ALL"})
            continue
        if wu_id not in started:
            issues.append({"code": "WU-MISSING-STARTED-EVENT", "severity": "error", "wu_id": wu_id, "detail": "no work_unit_started event"})
        if wu_id not in completed:
            issues.append({"code": "WU-MISSING-COMPLETED-EVENT", "severity": "error", "wu_id": wu_id, "detail": "no work_unit_completed event"})
        ev_rel = wu.get("evidence_path")
        if not ev_rel or not (rd / ev_rel).is_file():
            issues.append({"code": "WU-MISSING-EVIDENCE", "severity": "error", "wu_id": wu_id, "detail": f"evidence_path={ev_rel!r} not found"})
        sc = wu.get("sources_collected")
        if status == "completed" and (not isinstance(sc, int) or sc <= 0):
            issues.append({"code": "WU-COMPLETED-WITHOUT-SOURCES", "severity": "error", "wu_id": wu_id, "detail": "status=completed requires sources_collected>0; use completed_no_sources for seed-only"})
        if status == "completed_no_sources" and isinstance(sc, int) and sc > 0:
            issues.append({"code": "WU-COMPLETED-NO-SOURCES-INCONSISTENT", "severity": "error", "wu_id": wu_id, "detail": "completed_no_sources but sources_collected>0"})
    if isinstance(summary, dict) and "_parse_error" not in summary:
        if summary.get("total_terminal") != summary.get("total_planned"):
            issues.append(
                {
                    "code": "WU-EXECUTION-SUMMARY-MISMATCH",
                    "severity": "error",
                    "detail": f"total_terminal={summary.get('total_terminal')} total_planned={summary.get('total_planned')}",
                }
            )
    elif planned_ids:
        warnings.append({"code": "WU-EXECUTION-SUMMARY-MISSING", "severity": "warning", "detail": "execution-summary.json missing"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, "WU completion gate")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
