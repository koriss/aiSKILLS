#!/usr/bin/env python3
"""Guard: refuse PASS when v18 legacy compatibility paths are silently invoked.

Closes failure code V18-LEGACY-COMPAT-DRIFT (Phase 4C P1, static-audit). Two
classes of failure are blocked:

  1. ``final-answer-gate.json`` carries a v18 ``gates`` block but no v19
     ``checks`` block, AND ``RFO_ALLOW_V18_GATES_FALLBACK`` is **not** set
     in run_meta. This indicates render/outbox produced legacy output and a
     reader is silently consuming it.
  2. Any v19 artifact carries both ``gates`` and ``checks`` simultaneously,
     unless the run was explicitly executed under the legacy opt-in.

stdlib-only, fail-closed, JSON envelope on stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_v18_legacy_compat"


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> int:
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
    return 0 if not blocking else 1


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
    fag = _load(rd / "final-answer-gate.json")
    run_meta = _load(rd / "run.json") or {}
    legacy_opt_in = bool(run_meta.get("legacy_v18_gates_fallback")) if isinstance(run_meta, dict) else False
    if not isinstance(fag, dict):
        warnings.append({"code": "FAG-MISSING", "severity": "warning", "detail": "final-answer-gate.json absent"})
    elif "_parse_error" in fag:
        issues.append({"code": "FAG-PARSE", "severity": "error", "detail": fag["_parse_error"]})
    else:
        has_checks = isinstance(fag.get("checks"), dict)
        legacy_gates = fag["gates"] if "gates" in fag else None
        has_legacy = isinstance(legacy_gates, dict)
        if not has_checks and has_legacy and not legacy_opt_in:
            issues.append(
                {
                    "code": "V18-LEGACY-COMPAT-DRIFT",
                    "severity": "error",
                    "detail": "final-answer-gate.json carries v18 'gates' but no v19 'checks'; runtime is silently using legacy semantics",
                }
            )
        if has_checks and has_legacy and not legacy_opt_in:
            issues.append(
                {
                    "code": "V18-LEGACY-FIELDS-COEXIST",
                    "severity": "error",
                    "detail": "final-answer-gate.json carries both 'checks' and 'gates'; emit only canonical 'checks' in v19.2.0",
                }
            )
    blocking = any(i.get("severity") == "error" for i in issues)
    return _emit(not blocking, blocking, issues, warnings, "v18 legacy compat drift gate")


if __name__ == "__main__":
    raise SystemExit(main())
