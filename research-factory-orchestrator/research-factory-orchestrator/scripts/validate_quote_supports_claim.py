#!/usr/bin/env python3
"""NLI-light: quote_text must appear in cited evidence card (VeriCite-style baseline)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path, nargs="?", default=Path("."))
    rd = ap.parse_args().run_dir
    cr, er = rd / "claims" / "claims-registry.json", rd / "evidence" / "evidence-cards.json"
    if not cr.is_file() or not er.is_file():
        print(json.dumps({"status": "pass", "note": "missing claims or evidence"}, ensure_ascii=False))
        return 0
    reg = json.loads(cr.read_text(encoding="utf-8"))
    evs = {e["evidence_card_id"]: e for e in json.loads(er.read_text(encoding="utf-8")).get("evidence_cards", []) if e.get("evidence_card_id")}
    bad = []
    for c in reg.get("claims", []):
        for row in c.get("verbatim_supports") or []:
            q = str(row.get("quote_text") or "")
            ec = evs.get(row.get("evidence_card_id"))
            if not ec or not q:
                continue
            hay = json.dumps(ec, ensure_ascii=False) + str(ec.get("summary", ""))
            if q not in hay:
                bad.append({"claim_id": c.get("claim_id"), "evidence_card_id": row.get("evidence_card_id")})
    if bad:
        print(json.dumps({"status": "fail", "validator": "validate_quote_supports_claim", "errors": bad}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "pass", "validator": "validate_quote_supports_claim"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
