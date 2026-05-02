#!/usr/bin/env python3
"""V2 — sacred path claim → evidence → source."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Must match schemas/core/claims-registry.schema.json → $defs/supportEntry.role_for_claim.enum
ROLE_FOR_CLAIM_ALLOWED = frozenset(
    {"primary_support", "corroboration", "context", "lead", "opposition"},
)


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_traceability",
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
    srcp = rd / "sources.json"
    if not srcp.is_file():
        srcp = rd / "sources" / "sources.json"
    src = _load(srcp) or {}
    items = src.get("sources") if isinstance(src.get("sources"), list) else src.get("items", [])
    sid_set = {str(s.get("source_id") or s.get("id") or "") for s in items if isinstance(s, dict)}
    sid_set.discard("")
    evb = _load(rd / "evidence-cards.json") or {}
    cards = {str(c.get("evidence_id")): c for c in (evb.get("evidence_cards") or []) if isinstance(c, dict)}
    cr = _load(rd / "claims-registry.json") or {}
    for cl in cr.get("claims") or []:
        if not isinstance(cl, dict):
            continue
        cid = str(cl.get("claim_id") or "")
        for eid in cl.get("evidence_card_ids") or []:
            if str(eid) not in cards:
                issues.append(
                    {
                        "code": "missing_evidence_card",
                        "severity": "error",
                        "path": f"claims/{cid}",
                        "detail": f"evidence_card_id {eid} not found",
                        "artifact": "claims-registry.json",
                    }
                )
        for sup in cl.get("support_set") or []:
            if not isinstance(sup, dict):
                continue
            role = str(sup.get("role_for_claim") or "").strip()
            if role not in ROLE_FOR_CLAIM_ALLOWED:
                issues.append(
                    {
                        "code": "TRACE-ROLE-001",
                        "severity": "error",
                        "path": cid,
                        "detail": f"invalid or missing role_for_claim: {role!r}",
                        "artifact": "claims-registry.json",
                    }
                )
            eid = str(sup.get("evidence_card_id") or "")
            ec = cards.get(eid)
            if not ec:
                issues.append({"code": "support_evidence_missing", "severity": "error", "path": cid, "detail": eid, "artifact": "claims-registry.json"})
                continue
            sup_sid = str(sup.get("source_id") or "")
            ec_sids = {str(x) for x in (ec.get("source_ids") or []) if x}
            if sup_sid and sup_sid not in ec_sids:
                issues.append(
                    {
                        "code": "TRACE-SUP-SOURCE-001",
                        "severity": "error",
                        "path": cid,
                        "detail": f"support_set source_id {sup_sid!r} not in evidence card {eid} source_ids",
                        "artifact": "claims-registry.json",
                    }
                )
            decl_eids = {str(x) for x in (cl.get("evidence_card_ids") or []) if x}
            if eid and eid not in decl_eids:
                issues.append(
                    {
                        "code": "TRACE-SUP-DECL-001",
                        "severity": "error",
                        "path": cid,
                        "detail": f"support_set evidence_card_id {eid!r} not in claim evidence_card_ids",
                        "artifact": "claims-registry.json",
                    }
                )
            ex = ec.get("extracted_fact_or_excerpt") or {}
            if not (isinstance(ex, dict) and str(ex.get("text") or "").strip()):
                issues.append({"code": "empty_excerpt", "severity": "error", "path": eid, "detail": "extracted_fact_or_excerpt.text empty", "artifact": "evidence-cards.json"})
            sids = ec.get("source_ids") or []
            if not sids:
                issues.append(
                    {
                        "code": "evidence_without_source",
                        "severity": "error",
                        "path": eid,
                        "detail": "evidence card has no source_ids",
                        "artifact": "evidence-cards.json",
                    }
                )
            for sid in sids:
                if str(sid) not in sid_set:
                    issues.append({"code": "unknown_source", "severity": "error", "path": eid, "detail": str(sid), "artifact": "evidence-cards.json"})
    blocking = bool(issues)
    _emit(not blocking, blocking, issues, warnings, "V2 traceability")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
