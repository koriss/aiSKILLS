#!/usr/bin/env python3
"""Emit ``validation/sacred-path-graph.json`` — PROV-style nodes/edges from core artifacts (v19.1, stdlib only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    out_dir = rd / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sacred-path-graph.json"

    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    srcp = rd / "sources.json"
    if not srcp.is_file():
        srcp = rd / "sources" / "sources.json"
    src = _load(srcp) or {}
    for s in src.get("sources") or []:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("source_id") or "")
        if not sid:
            continue
        nid = f"source:{sid}"
        u = str(s.get("url") or "")
        host = ""
        try:
            host = urlparse(u).hostname or ""
        except Exception:
            host = ""
        nodes.append({"id": nid, "kind": "prov:Entity", "label": sid, "url": u, "host": host})

    ev = _load(rd / "evidence-cards.json") or {}
    for c in ev.get("evidence_cards") or []:
        if not isinstance(c, dict):
            continue
        eid = str(c.get("evidence_id") or "")
        if not eid:
            continue
        nid = f"evidence:{eid}"
        nodes.append({"id": nid, "kind": "prov:Entity", "label": eid, "evidence_type": str(c.get("evidence_type") or "")})
        for sid in c.get("source_ids") or []:
            sid = str(sid)
            if sid:
                edges.append({"from": f"source:{sid}", "to": nid, "role": "wasDerivedFrom"})

    cr = _load(rd / "claims-registry.json") or {}
    for cl in cr.get("claims") or []:
        if not isinstance(cl, dict):
            continue
        cid = str(cl.get("claim_id") or "")
        if not cid:
            continue
        nid = f"claim:{cid}"
        nodes.append({"id": nid, "kind": "prov:Entity", "label": cid})
        for eid in cl.get("evidence_card_ids") or []:
            eid = str(eid)
            if eid:
                edges.append({"from": f"evidence:{eid}", "to": nid, "role": "wasDerivedFrom"})
        for sup in cl.get("support_set") or []:
            if not isinstance(sup, dict):
                continue
            sid = str(sup.get("source_id") or "")
            eid = str(sup.get("evidence_card_id") or "")
            if sid:
                edges.append({"from": f"source:{sid}", "to": nid, "role": str(sup.get("role_for_claim") or "support")})
            if eid:
                edges.append({"from": f"evidence:{eid}", "to": nid, "role": str(sup.get("role_for_claim") or "support")})

    fg = _load(rd / "final-answer-gate.json") or {}
    if fg:
        nodes.append({"id": "artifact:final-answer-gate", "kind": "prov:Entity", "label": "final-answer-gate.json"})
        for cl in cr.get("claims") or []:
            if isinstance(cl, dict) and cl.get("claim_id"):
                edges.append({"from": f"claim:{cl['claim_id']}", "to": "artifact:final-answer-gate", "role": "wasInformedBy"})

    doc = {
        "schema_version": "v19.1",
        "prov_profile": "w3c-prov-alignment-lite",
        "nodes": nodes,
        "edges": edges,
    }
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "path": str(out_path), "nodes": len(nodes), "edges": len(edges)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
