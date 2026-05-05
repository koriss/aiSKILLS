#!/usr/bin/env python3
"""
Dev-only: copy a v19 good fixture run-dir and append N unrelated sources + evidence_cards.

Does not modify the canonical fixtures in-repo unless --in-place (discouraged).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def _copy_fixture(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture", required=True, type=Path, help="Path to fixture directory (e.g. good/mvr_minimal_valid)")
    ap.add_argument("--out", required=True, type=Path, help="Output run-directory")
    ap.add_argument("--n", type=int, default=10, help="Number of noise sources/cards to add")
    ap.add_argument("--in-place", action="store_true", help="Overwrite --out in place (dangerous)")
    args = ap.parse_args()
    src = args.fixture.resolve()
    out = args.out.resolve()
    if not src.is_dir():
        print(json.dumps({"error": "missing_fixture", "path": str(src)}), file=sys.stderr)
        return 1
    if args.in_place and out == src:
        _copy_fixture(src, out)
    else:
        _copy_fixture(src, out)
    n = max(0, int(args.n))
    sp = out / "sources.json"
    if not sp.is_file():
        print(json.dumps({"error": "missing_sources_json", "path": str(sp)}), file=sys.stderr)
        return 1
    src_obj = json.loads(sp.read_text(encoding="utf-8"))
    sources = list(src_obj.get("sources") or [])
    evp = out / "evidence-cards.json"
    if not evp.is_file():
        print(json.dumps({"error": "missing_evidence_cards", "path": str(evp)}), file=sys.stderr)
        return 1
    ev_obj = json.loads(evp.read_text(encoding="utf-8"))
    cards = list(ev_obj.get("evidence_cards") or [])
    base = len(sources)
    for i in range(n):
        idx = base + i + 1
        sid = f"NOISE_S{idx}"
        eid = f"NOISE_E{idx}"
        sources.append(
            {
                "source_id": sid,
                "title": f"noise-title-{idx}",
                "canonical_origin_id": f"noise-origin-{idx}",
                "url": f"https://noise.example.invalid/{idx}",
                "publisher": "noise",
                "accessed_at": "2026-05-02T12:00:00Z",
                "source_role": "journalist",
                "access_level": "secondary",
                "interest_alignment": "unknown",
                "verification_mode": "aggregation",
                "independence": "high",
                "citation_eligible": True,
                "corroboration_type": "independent",
            }
        )
        cards.append(
            {
                "evidence_id": eid,
                "source_ids": [sid],
                "evidence_type": "article",
                "extracted_fact_or_excerpt": {"kind": "excerpt", "text": f"noise excerpt {idx}"},
                "supports": "context_only",
                "confidence": "low",
            }
        )
    src_obj["sources"] = sources
    sp.write_text(json.dumps(src_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ev_obj["evidence_cards"] = cards
    evp.write_text(json.dumps(ev_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "out": str(out), "added": n}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
