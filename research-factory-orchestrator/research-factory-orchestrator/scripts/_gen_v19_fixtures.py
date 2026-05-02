#!/usr/bin/env python3
"""One-shot generator for tests/fixtures/v19 (good + bad). Stdlib only."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "v19"
RUN_VERSION = "19.0.1"


def profile_used(profile_name: str) -> dict:
    p = ROOT / "validation-profiles" / f"{profile_name}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return {
        "profile": profile_name,
        "schema_version": data.get("schema_version"),
        "options": data.get("options") if isinstance(data.get("options"), dict) else {},
    }


def _sha() -> str:
    return "0" * 64


def src_bundle(s1: str, s2: str, o1: str, o2: str) -> dict:
    def one(sid: str, oid: str) -> dict:
        return {
            "source_id": sid,
            "title": f"T-{sid}",
            "canonical_origin_id": oid,
            "url": f"https://example.invalid/{sid}",
            "publisher": "fixture",
            "accessed_at": "2026-05-02T12:00:00Z",
            "source_role": "news_media",
            "access_level": "public",
            "interest_alignment": "unknown",
            "verification_mode": "secondary",
            "independence": "independent",
            "citation_eligible": True,
            "corroboration_type": "corroborating",
        }

    return {"schema_version": "v19.0", "sources": [one(s1, o1), one(s2, o2)]}


def ev_card(eid: str, sids: list[str], text: str, etype: str) -> dict:
    return {
        "schema_version": "v19.0",
        "evidence_cards": [
            {
                "evidence_id": eid,
                "source_ids": sids,
                "evidence_type": etype,
                "extracted_fact_or_excerpt": {"kind": "excerpt", "text": text or "x"},
                "supports": [{"claim_id": "C1", "stance": "supports"}],
                "confidence": "medium",
            }
        ],
    }


def claim_row(ctype: str, status: str, eids: list[str], support: list[dict], **extra: object) -> dict:
    row: dict = {
        "claim_id": "C1",
        "claim_text": "fixture",
        "claim_type": ctype,
        "status": status,
        "confidence": "high" if status == "confirmed_fact" else "medium",
        "evidence_card_ids": eids,
        "support_set": support,
    }
    row.update({k: v for k, v in extra.items() if v is not None})
    return {"schema_version": "v19.0", "claims": [row]}


def gate(blocking: list | None = None, hs: str | bool = False) -> dict:
    return {
        "schema_version": "v19.0",
        "run_id": "fx",
        "passed": not bool(blocking),
        "checks": {},
        "contradiction_echo": {
            "contradiction_level": 0,
            "contradiction_scan_performed": True,
            "scan_scope": "L0",
            "high_severity_detected": hs,
        },
        "overconfidence_risk": {"blocking": blocking or [], "warnings": [], "signals": {}},
        "created_at": "2026-05-02T12:00:00Z",
    }


def dm(cli: bool, **extra: object) -> dict:
    o = {
        "schema_version": "v19.0",
        "run_id": "fx",
        "delivery_status": "not_queued",
        "attachments": [{"path": "report/full-report.html", "sha256": _sha()}],
        "local_paths_exposed": False,
        "artifact_ready_claim_allowed": True,
        "external_delivery_claim_allowed": not cli,
        "stub_delivery_disclosure_required": False,
        "provider_capability_snapshot": {"cli": cli},
        "real_external_delivery": False if cli else True,
        "stub_delivery": False,
        "created_at": "2026-05-02T12:00:00Z",
    }
    o.update(extra)
    return o


def write_dir(rd: Path, files: dict[str, object]) -> None:
    rd.mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        p = rd / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, (dict, list)):
            p.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            p.write_text(str(body), encoding="utf-8")


def common_html() -> str:
    return "<!DOCTYPE html><html><body>" + ("x" * 120) + "</body></html>\n"


def main() -> None:
    if FIX.exists():
        shutil.rmtree(FIX)
    sup = [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}]
    good_files = {
        "run.json": {"run_id": "fx", "provider": "cli", "mode": "research", "version": RUN_VERSION},
        "validation-profile-used.json": profile_used("mvr"),
        "sources.json": src_bundle("S1", "S2", "oa", "ob"),
        "evidence-cards.json": ev_card("E1", ["S1"], "ok", "article"),
        "claims-registry.json": claim_row("narrative_claim", "reported_claim", ["E1"], sup),
        "final-answer-gate.json": gate(),
        "delivery-manifest.json": dm(True),
        "validation-transcript.json": {"schema_version": "v19.0", "status": "pending", "validators": []},
        "report/full-report.html": common_html(),
    }
    write_dir(FIX / "good" / "mvr_minimal_valid", good_files)

    def b(name: str, files: dict[str, object]) -> None:
        write_dir(FIX / "bad" / name, files)

    base = {
        "run.json": {"run_id": "fx", "provider": "cli", "mode": "research", "version": RUN_VERSION},
        "validation-profile-used.json": profile_used("mvr"),
        "sources.json": src_bundle("S1", "S2", "oa", "ob"),
        "final-answer-gate.json": gate(),
        "delivery-manifest.json": dm(True),
        "validation-transcript.json": {"schema_version": "v19.0", "status": "pending", "validators": []},
        "report/full-report.html": common_html(),
    }

    b(
        "claim_without_evidence",
        {
            **base,
            "evidence-cards.json": {"schema_version": "v19.0", "evidence_cards": []},
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "evidence_without_source",
        {
            **base,
            "evidence-cards.json": ev_card("E1", [], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "evidence_source_id_unknown",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S_MISSING"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "confirmed_from_social_only",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "tweet", "social_post"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "confirmed_fact",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "forecast_as_confirmed_fact",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "forecast",
                "confirmed_fact",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "geopolitical_intent_as_confirmed_fact",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "geopolitical_intent_assessment",
                "confirmed_fact",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "raw_visual_without_context_confirmed",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "caption", "user_video"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "confirmed_fact",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    b(
        "kb_match_used_as_evidence",
        {
            **base,
            "sources.json": src_bundle("KB:001", "S2", "kbx", "ob"),
            "evidence-cards.json": ev_card("E1", ["KB:001"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "confirmed_fact",
                ["E1"],
                [{"source_id": "KB:001", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        },
    )

    dup_sources = {
        "schema_version": "v19.0",
        "sources": [
            {
                "source_id": "S1",
                "title": "A",
                "canonical_origin_id": "same",
                "url": "https://example.invalid/1",
                "publisher": "x",
                "accessed_at": "2026-05-02T12:00:00Z",
                "source_role": "news_media",
                "access_level": "public",
                "interest_alignment": "unknown",
                "verification_mode": "secondary",
                "independence": "independent",
                "citation_eligible": True,
                "corroboration_type": "corroborating",
            },
            {
                "source_id": "S2",
                "title": "B",
                "canonical_origin_id": "same",
                "url": "https://example.invalid/2",
                "publisher": "x",
                "accessed_at": "2026-05-02T12:00:00Z",
                "source_role": "news_media",
                "access_level": "public",
                "interest_alignment": "unknown",
                "verification_mode": "secondary",
                "independence": "independent",
                "citation_eligible": True,
                "corroboration_type": "corroborating",
            },
        ],
    }
    dup_ev = {
        "schema_version": "v19.0",
        "evidence_cards": [
            {
                "evidence_id": "E1",
                "source_ids": ["S1"],
                "extracted_fact_or_excerpt": {"kind": "excerpt", "text": "a"},
                "supports": [{"claim_id": "C1", "stance": "supports"}],
                "confidence": "medium",
            },
            {
                "evidence_id": "E2",
                "source_ids": ["S2"],
                "extracted_fact_or_excerpt": {"kind": "excerpt", "text": "b"},
                "supports": [{"claim_id": "C1", "stance": "supports"}],
                "confidence": "medium",
            },
        ],
    }
    dup_claim = {
        "schema_version": "v19.0",
        "claims": [
            {
                "claim_id": "C1",
                "claim_text": "dup",
                "claim_type": "narrative_claim",
                "status": "reported_claim",
                "confidence": "medium",
                "evidence_card_ids": ["E1", "E2"],
                "support_set": [
                    {"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"},
                    {"source_id": "S2", "evidence_card_id": "E2", "role_for_claim": "corroboration"},
                ],
            }
        ],
    }
    b(
        "duplicate_sources_counted_as_independent",
        {**base, "sources.json": dup_sources, "evidence-cards.json": dup_ev, "claims-registry.json": dup_claim},
    )

    b(
        "final_answer_new_fact",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
            "final-answer-gate.json": gate(["new_fact_without_claim_id"]),
        },
    )

    b(
        "local_path_in_user_message",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
            "delivery-manifest.json": dm(True, user_visible_artifact_paths=["/home/x/y.txt"]),
        },
    )

    b(
        "cli_claimed_external_delivery",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
            "delivery-manifest.json": dm(False),
        },
    )

    b(
        "contradiction_required_but_missing",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
                meta={"force_contradictions_lite": True},
            ),
        },
    )

    b(
        "l0_scan_unknown_under_full_profile",
        {
            **base,
            "validation-profile-used.json": profile_used("full-rigor"),
            "contradictions-lite.json": {"schema_version": "v19.0", "pairs": []},
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
            "final-answer-gate.json": gate(hs="unknown"),
        },
    )

    rel_files = {k: v for k, v in base.items() if k != "validation-transcript.json"}
    rel_files.update(
        {
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
        }
    )
    b("release_pass_without_transcript", rel_files)

    b(
        "support_set_role_invalid",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "totally_made_up"}],
            ),
        },
    )

    b(
        "cli_with_external_delivery_claim_allowed",
        {
            **base,
            "evidence-cards.json": ev_card("E1", ["S1"], "t", "article"),
            "claims-registry.json": claim_row(
                "narrative_claim",
                "reported_claim",
                ["E1"],
                [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            ),
            "delivery-manifest.json": dm(True, external_delivery_claim_allowed=True, real_external_delivery=False),
        },
    )


if __name__ == "__main__":
    main()
