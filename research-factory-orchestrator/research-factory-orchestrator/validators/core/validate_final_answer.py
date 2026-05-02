#!/usr/bin/env python3
"""V5 — overconfidence_risk.blocking must be empty for pass."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_final_answer",
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    fg_path = rd / "final-answer-gate.json"
    if not fg_path.is_file():
        issues.append({"code": "missing_gate", "severity": "error", "path": str(fg_path), "detail": "missing", "artifact": "final-answer-gate.json"})
    else:
        try:
            fg = json.loads(fg_path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({"code": "gate_parse", "severity": "error", "path": str(fg_path), "detail": str(e), "artifact": "final-answer-gate.json"})
            fg = {}
        ocr = fg.get("overconfidence_risk") if isinstance(fg, dict) else None
        if isinstance(ocr, dict):
            for code in ocr.get("blocking") or []:
                issues.append({"code": str(code), "severity": "error", "path": "overconfidence_risk.blocking", "detail": str(code), "artifact": "final-answer-gate.json"})
            for w in ocr.get("warnings") or []:
                warnings.append({"code": str(w), "severity": "warning", "path": "overconfidence_risk.warnings", "detail": str(w), "artifact": "final-answer-gate.json"})
    blocking = bool(issues)
    _emit(not blocking, blocking, issues, warnings, "V5 final answer / overconfidence")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
