#!/usr/bin/env python3
"""GSAR-lite typed grounding: 4-way claim partition, weighted S, advisory decision (stdlib only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RHO = 0.5
ETYPE_W: dict[str, float] = {
    "tool_match": 1.0,
    "structured_data": 0.95,
    "document": 0.85,
    "article": 0.85,
    "snippet": 0.70,
    "social_post": 0.60,
    "user_video": 0.60,
    "kb": 0.0,
    "kb_match": 0.0,
}


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def _ev_weight(card: dict) -> float:
    et = str(card.get("evidence_type") or "").strip()
    return ETYPE_W.get(et, 0.75)


def _claim_ids_in_registry(cr: dict) -> set[str]:
    out: set[str] = set()
    for cl in cr.get("claims") or []:
        if isinstance(cl, dict) and cl.get("claim_id"):
            out.add(str(cl["claim_id"]))
    return out


def _high_contradiction_claim_ids(clite: dict) -> set[str]:
    out: set[str] = set()
    for ent in clite.get("entries") or []:
        if not isinstance(ent, dict):
            continue
        sev = str(ent.get("severity") or "")
        if sev in ("high", "critical"):
            cid = str(ent.get("claim_id") or "")
            if cid:
                out.add(cid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    out_dir = rd / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "typed-grounding-report.json"

    cr = _load(rd / "claims-registry.json") or {}
    evb = _load(rd / "evidence-cards.json") or {}
    cards = {str(c.get("evidence_id")): c for c in (evb.get("evidence_cards") or []) if isinstance(c, dict)}
    clite = _load(rd / "contradictions-lite.json") or {"entries": []}
    claim_ids = _claim_ids_in_registry(cr)
    hi_contra = _high_contradiction_claim_ids(clite)

    partitions: list[dict] = []
    Wg = Wu = Wx = Wk = 0.0
    inflation: list[str] = []

    for cid in sorted(hi_contra):
        if cid not in claim_ids:
            inflation.append(cid)

    for cl in cr.get("claims") or []:
        if not isinstance(cl, dict):
            continue
        cid = str(cl.get("claim_id") or "")
        sups = [s for s in (cl.get("support_set") or []) if isinstance(s, dict)]
        roles = {str(s.get("role_for_claim") or "") for s in sups}
        has_primary = "primary_support" in roles
        has_corr = "corroboration" in roles

        if cid in hi_contra:
            cls = "contradicted"
            w = max((_ev_weight(cards.get(str(s.get("evidence_card_id")) or "") or {}) for s in sups), default=0.75)
            if not sups:
                w = 0.75
            Wx += w
        elif has_primary:
            cls = "grounded"
            pw = 0.0
            for s in sups:
                if str(s.get("role_for_claim") or "") != "primary_support":
                    continue
                ec = cards.get(str(s.get("evidence_card_id") or "")) or {}
                pw = max(pw, _ev_weight(ec))
            Wg += max(pw, 0.01)
        elif has_corr:
            cls = "complementary"
            cw = 0.0
            for s in sups:
                if str(s.get("role_for_claim") or "") != "corroboration":
                    continue
                ec = cards.get(str(s.get("evidence_card_id") or "")) or {}
                cw = max(cw, _ev_weight(ec))
            Wk += max(cw, 0.01)
        else:
            cls = "ungrounded"
            uw = 0.0
            for s in sups:
                ec = cards.get(str(s.get("evidence_card_id") or "")) or {}
                uw = max(uw, _ev_weight(ec))
            Wu += max(uw, 0.01) if sups else 0.05

        partitions.append({"claim_id": cid or "?", "partition": cls})

    den = Wg + Wu + RHO * Wx + Wk
    if den <= 0:
        s_score = 1.0
    else:
        s_score = (Wg + Wk) / den

    if s_score >= 0.80:
        decision = "proceed"
    elif s_score >= 0.65:
        decision = "regenerate"
    else:
        decision = "replan"

    report = {
        "schema_version": "v19.1",
        "checker_id": "typed_grounding_gsar_lite",
        "rho": RHO,
        "weights_by_partition": {"G": Wg, "U": Wu, "X": Wx, "K": Wk},
        "S": round(s_score, 6),
        "decision_advisory": decision,
        "claim_partitions": partitions,
        "typed_groundedness_inflation": inflation,
        "codes": (["TYPED-GROUNDEDNESS-INFLATION"] if inflation else []),
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(out_path), "S": s_score, "decision_advisory": decision}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
