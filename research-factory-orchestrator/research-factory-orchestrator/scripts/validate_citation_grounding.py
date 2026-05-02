#!/usr/bin/env python3
"""Validate claim → evidence/source grounding (VeriCite-style verbatim_supports; GaRAGe/FaithEval)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _j(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path, nargs="?", default=Path("."))
    args = ap.parse_args()
    rd = args.run_dir

    reg = _j(rd / "claims" / "claims-registry.json", {})
    claims = reg.get("claims", [])
    if not claims:
        print(
            json.dumps(
                {"status": "pass", "validator": "validate_citation_grounding", "note": "no claims to validate"},
                ensure_ascii=False,
            )
        )
        return 0

    ev_cards = _j(rd / "evidence" / "evidence-cards.json", {}).get("evidence_cards", [])
    src_rows = _j(rd / "sources" / "sources.json", {}).get("sources", [])
    ev_by_id = {str(r.get("evidence_card_id")): r for r in ev_cards if r.get("evidence_card_id")}
    ev_ids = set(ev_by_id)
    src_ids = {str(r.get("source_id")) for r in src_rows if r.get("source_id")}
    failures: list[dict] = []

    for c in claims:
        cid = c.get("claim_id")
        status = str(c.get("status") or "")
        c_evs = [str(x) for x in (c.get("evidence_card_ids") or []) if x]
        c_src = [str(x) for x in (c.get("source_ids") or []) if x]
        missing_evs = [x for x in c_evs if x not in ev_ids]
        missing_src = [x for x in c_src if x not in src_ids]
        if missing_evs or missing_src:
            failures.append(
                {
                    "claim_id": cid,
                    "reason": "dangling_reference",
                    "missing_evidence_card_ids": missing_evs,
                    "missing_source_ids": missing_src,
                }
            )
        if status == "confirmed" and (not c_evs or not c_src):
            failures.append(
                {
                    "claim_id": cid,
                    "reason": "confirmed_without_full_grounding",
                    "evidence_card_ids": c_evs,
                    "source_ids": c_src,
                }
            )
        vs = c.get("verbatim_supports") or []
        if status == "confirmed":
            if not vs:
                failures.append({"claim_id": cid, "reason": "confirmed_missing_verbatim_supports"})
            for row in vs:
                ecid = str(row.get("evidence_card_id") or "")
                card = ev_by_id.get(ecid)
                q = str(row.get("quote_text") or "")
                if not card or not q:
                    failures.append({"claim_id": cid, "reason": "verbatim_support_incomplete", "evidence_card_id": ecid})
                    continue
                summ = str(card.get("summary") or "")
                ex = str(card.get("excerpt") or "")
                blob = summ + ex + json.dumps(card, ensure_ascii=False)
                if q not in blob:
                    failures.append({"claim_id": cid, "reason": "quote_not_substring_of_evidence_card", "evidence_card_id": ecid})
        if status == "disputed" and not (c.get("contradicting_evidence_ids") or c.get("contradicting_evidence_card_ids")):
            failures.append({"claim_id": cid, "reason": "disputed_missing_contradicting_evidence"})

    if failures:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "validator": "validate_citation_grounding",
                    "failures": failures[:50],
                    "failure_count": len(failures),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "validator": "validate_citation_grounding",
                "claims_checked": len(claims),
                "evidence_cards": len(ev_cards),
                "sources": len(src_rows),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
