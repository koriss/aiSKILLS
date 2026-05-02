#!/usr/bin/env python3
"""V6 — delivery manifest split fields + CLI external invariant + path leak list."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_delivery_truth",
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
    run = {}
    if (rd / "run.json").is_file():
        try:
            run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        except Exception:
            run = {}
    prov = str(run.get("provider") or "").lower()
    dm: dict = {}
    dm_path = rd / "delivery-manifest.json"
    if not dm_path.is_file():
        issues.append({"code": "missing_dm", "severity": "error", "path": str(dm_path), "detail": "missing", "artifact": "delivery-manifest.json"})
    else:
        try:
            dm = json.loads(dm_path.read_text(encoding="utf-8"))
            if not isinstance(dm, dict):
                dm = {}
        except Exception as e:
            issues.append({"code": "dm_parse", "severity": "error", "path": str(dm_path), "detail": str(e), "artifact": "delivery-manifest.json"})
            dm = {}
        if isinstance(dm, dict):
            if prov == "cli" and dm.get("real_external_delivery") is True:
                issues.append({"code": "cli_external", "severity": "error", "path": "real_external_delivery", "detail": "cli forbids true", "artifact": "delivery-manifest.json"})
            if prov == "cli" and dm.get("external_delivery_claim_allowed") is True:
                issues.append(
                    {
                        "code": "DELIV-EXT-CLI",
                        "severity": "error",
                        "path": "external_delivery_claim_allowed",
                        "detail": "cli forbids external delivery claim",
                        "artifact": "delivery-manifest.json",
                    }
                )
            for pth in dm.get("user_visible_artifact_paths") or []:
                if isinstance(pth, str) and re.search(r"(^|/)(home|Users|tmp|var|root)/", pth, re.I):
                    issues.append({"code": "local_path_leak", "severity": "error", "path": pth, "detail": "absolute path in user-visible list", "artifact": "delivery-manifest.json"})
    vt = rd / "validation-transcript.json"
    if vt.is_file():
        try:
            tr = json.loads(vt.read_text(encoding="utf-8"))
        except Exception:
            tr = {}
        if isinstance(tr, dict) and str(tr.get("status") or "").lower() == "fail":
            if isinstance(dm, dict) and str(dm.get("delivery_status") or "") not in ("failed", "validation_failed", "cancelled"):
                issues.append({"code": "rollback_not_explicit", "severity": "error", "path": "delivery_status", "detail": str(dm.get("delivery_status")), "artifact": "delivery-manifest.json"})
    blocking = bool(issues)
    _emit(not blocking, blocking, issues, warnings, "V6 delivery truth")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
