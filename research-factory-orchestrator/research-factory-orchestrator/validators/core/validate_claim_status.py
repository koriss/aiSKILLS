#!/usr/bin/env python3
"""V4 — status caps, contradiction-lite obligation, L0 scan under full profile."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_claim_status",
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


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    prof = _load(rd / "validation-profile-used.json") or {}
    profile = str(prof.get("profile") or "mvr")
    opts = prof.get("options") if isinstance(prof.get("options"), dict) else {}
    req_lite = opts.get("require_full_contradiction_matrix") is True or any(
        isinstance(c, dict) and (c.get("meta") or {}).get("force_contradictions_lite") for c in (_load(rd / "claims-registry.json") or {}).get("claims") or []
    )
    if req_lite and not (rd / "contradictions-lite.json").is_file():
        issues.append({"code": "contradictions_lite_required", "severity": "error", "path": "", "detail": "missing contradictions-lite.json", "artifact": ""})
    evb = _load(rd / "evidence-cards.json") or {}
    cards = {str(c.get("evidence_id")): c for c in (evb.get("evidence_cards") or []) if isinstance(c, dict)}
    fg = _load(rd / "final-answer-gate.json") or {}
    echo = fg.get("contradiction_echo") or {}
    if profile == "full-rigor" and echo.get("high_severity_detected") == "unknown":
        issues.append({"code": "l0_unknown_blocked", "severity": "error", "path": "final-answer-gate.json", "detail": "high_severity_detected unknown", "artifact": "final-answer-gate.json"})
    for cl in (_load(rd / "claims-registry.json") or {}).get("claims") or []:
        if not isinstance(cl, dict):
            continue
        st = str(cl.get("status") or "")
        ct = str(cl.get("claim_type") or "")
        if ct == "forecast" and st == "confirmed_fact":
            issues.append({"code": "forecast_status_cap", "severity": "error", "path": "C1", "detail": ct, "artifact": "claims-registry.json"})
        if ct == "geopolitical_intent_assessment" and st == "confirmed_fact":
            issues.append({"code": "geo_status_cap", "severity": "error", "path": "C1", "detail": ct, "artifact": "claims-registry.json"})
        for sup in cl.get("support_set") or []:
            if not isinstance(sup, dict):
                continue
            role = str(sup.get("role_for_claim") or "")
            eid = str(sup.get("evidence_card_id") or "")
            ec = cards.get(eid) or {}
            et = str(ec.get("evidence_type") or "")
            if st == "confirmed_fact" and et == "social_post":
                issues.append({"code": "social_post_confirmed", "severity": "error", "path": eid, "detail": et, "artifact": "evidence-cards.json"})
            if st == "confirmed_fact" and et == "user_video":
                issues.append({"code": "raw_visual_confirmed", "severity": "error", "path": eid, "detail": et, "artifact": "evidence-cards.json"})
            if st == "confirmed_fact" and role in ("lead", "lead_only", "snippet_only"):
                issues.append({"code": "weak_role_confirmed", "severity": "error", "path": role, "detail": "lead/snippet cannot back confirmed_fact", "artifact": "claims-registry.json"})
    blocking = bool(issues)
    _emit(not blocking, blocking, issues, warnings, "V4 claim status")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
