#!/usr/bin/env python3
"""MARCH-inspired blinded checker: derive numeric atoms from evidence only, compare to claim text (stdlib only)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


def _extract_numbers(text: str) -> list[str]:
    if not text:
        return []
    return _NUM_RE.findall(text)


def _evidence_text(card: dict) -> str:
    ex = card.get("extracted_fact_or_excerpt")
    if isinstance(ex, dict):
        if ex.get("kind") == "excerpt":
            return str(ex.get("text") or "")
        if ex.get("kind") in ("fact", "structured_fact"):
            return str(ex.get("text") or ex.get("value") or "")
    # legacy shapes
    if isinstance(card.get("excerpt"), str):
        return str(card["excerpt"])
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    out_dir = rd / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "blinded-checker-report.json"

    evb = _load(rd / "evidence-cards.json") or {}
    cr = _load(rd / "claims-registry.json") or {}
    cards = {str(c.get("evidence_id")): c for c in (evb.get("evidence_cards") or []) if isinstance(c, dict)}
    rows: list[dict] = []
    mismatches: list[str] = []

    for cl in cr.get("claims") or []:
        if not isinstance(cl, dict):
            continue
        cid = str(cl.get("claim_id") or "")
        claim_text = str(cl.get("claim_text") or "")
        asserted = _extract_numbers(claim_text)
        ev_chunks: list[str] = []
        for sup in cl.get("support_set") or []:
            if not isinstance(sup, dict):
                continue
            eid = str(sup.get("evidence_card_id") or "")
            ec = cards.get(eid) or {}
            ev_chunks.append(_evidence_text(ec))
        blinded_pool = " ".join(ev_chunks)
        blinded = _extract_numbers(blinded_pool)
        blinded_set = set(blinded)
        asserted_set = set(asserted)

        if not asserted_set and not blinded_set:
            match = "undecidable"
            bv = ""
            av = ""
        elif not asserted_set:
            match = "undecidable"
            bv = "|".join(sorted(blinded_set))
            av = ""
        elif not blinded_set:
            match = "undecidable"
            bv = ""
            av = "|".join(sorted(asserted_set))
        else:
            missing = [a for a in sorted(asserted_set) if a not in blinded_set]
            if missing:
                match = "false"
                mismatches.append(cid)
            else:
                match = "true"
            bv = "|".join(sorted(blinded_set))
            av = "|".join(sorted(asserted_set))

        rows.append(
            {
                "claim_id": cid or "?",
                "blinded_value": bv,
                "asserted_value": av,
                "match": match,
            }
        )

    report = {
        "schema_version": "v19.1",
        "checker_id": "blinded_checker",
        "claims": rows,
        "mismatch_claim_ids": mismatches,
        "overall_match": len(mismatches) == 0,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(out_path), "overall_match": report["overall_match"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
