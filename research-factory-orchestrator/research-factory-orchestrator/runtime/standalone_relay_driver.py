"""Standalone relay driver helpers (retired CLI was ``scripts/run_rfo_full_research.py``).

Operators must use ``scripts/rfo_execute.py``. This module keeps claim/matrix/gate helpers
used by unit tests and historical artifact tags — not a second execution path.
"""
from __future__ import annotations

from pathlib import Path

from runtime.citation_grounding import evaluate as citation_grounding_evaluate
from runtime.pkg_required_scaffold import ensure_pkg_required_paths
from runtime.schema_defaults import minimal_valid
from runtime.status import VERSION
from runtime.util import jr, jw, now

# Preserved in ``final-answer-gate.json`` checks for corpus/tests that fingerprint the old driver.
STANDALONE_DRIVER_ARTIFACT_TAG = "run_rfo_full_research"


def make_claims(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    """Convert sources → RFO-style claims + evidence cards."""
    STATUS_MAP = {"raw_document": "reported_claim"}

    def conf(s: dict) -> str:
        return "high" if s.get("verification_mode") == "raw_document" else "medium"

    claims: list[dict] = []
    evidence: list[dict] = []
    for s in sources:
        c = (s.get("content_snippet") or s.get("content") or "").strip()
        if not c:
            continue
        cid = f"C-{s['source_id']}"
        ev_id = f"EV-{s['source_id']}"
        sid_val = s["source_id"]

        claims.append({
            "claim_id": cid,
            "claim_text": c[:800],
            "claim_type": "source_derived",
            "status": STATUS_MAP.get(s.get("verification_mode", "testimony"), "inferred_assessment"),
            "confidence": conf(s),
            "evidence_card_ids": [ev_id],
            "support_set": [{"source_id": sid_val, "evidence_card_id": ev_id, "role_for_claim": "primary_support"}],
        })
        evidence.append({
            "evidence_id": ev_id,
            "source_ids": [sid_val],
            "claim_ids": [cid],
            "extracted_fact_or_excerpt": {"kind": "excerpt", "text": c[:400]},
            "supports": "direct",
            "confidence": conf(s),
        })
    return claims, evidence


def feature_matrix_standalone(run_id: str, collection: dict) -> dict:
    """Honest capability matrix for CLI relay driver (mode=research, not production dossier)."""
    web_ok = bool(collection.get("web_search_succeeded") or collection.get("external_web_search_executed"))
    return {
        "run_id": run_id,
        "version": VERSION,
        "generated_at": now(),
        "features": {
            "skill_discovery_frontmatter": "implemented",
            "interface_adapter": "implemented_scaffold",
            "runtime_job_worker": "not_applicable",
            "outbox_delivery_worker": "implemented",
            "wave_graph_collector": "implemented_seed_only",
            "real_external_search_workers": "implemented_real" if web_ok else "implemented_seed_only",
            "provider_outbound_real_send": "stub",
            "late_result_protocol": "implemented_scaffold",
            "deterministic_html_renderer": "implemented",
            "analytical_memo": "implemented_scaffold",
            "factual_dossier": "implemented_scaffold",
            "io_propaganda_check": "implemented_scaffold",
            "self_audit": "implemented_scaffold",
            "external_collector": "implemented_real" if web_ok else "implemented_seed_only",
            "work_unit_decomposition": "not_applicable",
            "work_unit_executor": "not_applicable",
        },
        "rule": (
            "Standalone relay driver (historical tag "
            + STANDALONE_DRIVER_ARTIFACT_TAG
            + "): relay-backed packaging; not a dossier production floor."
        ),
        "collection_summary": {
            "backend": collection.get("backend"),
            "external_web_search_executed": collection.get("external_web_search_executed", False),
            "external_source_packet_loaded": collection.get("external_source_packet_loaded", False),
            "web_search_attempted": collection.get("web_search_attempted", False),
            "web_search_succeeded": collection.get("web_search_succeeded", False),
            "web_search_result_count": collection.get("web_search_result_count", 0),
            "external_source_count": collection.get("external_source_count", 0),
            "seed_only": collection.get("seed_only", False),
        },
    }


def post_finish_standalone(rd: Path, entry: dict, profile_name: str) -> dict:
    """Scaffold missing package paths, run citation grounding, sync matrix + final gate."""
    run_id = str(entry["run_id"])
    job_id = str(entry["job_id"])
    cmd_id = str(entry["command_id"])
    ensure_pkg_required_paths(rd, run_id, job_id, cmd_id)
    cg = citation_grounding_evaluate(rd, run_id=run_id, job_id=job_id, profile=profile_name)
    col = jr(rd / "collection-result.json", {})
    fm = jr(rd / "feature-truth-matrix.json", {})
    if not isinstance(fm, dict):
        fm = feature_matrix_standalone(run_id, col if isinstance(col, dict) else {})
    fm["collection_summary"] = {
        "backend": col.get("backend") if isinstance(col, dict) else None,
        "external_web_search_executed": bool(col.get("external_web_search_executed")) if isinstance(col, dict) else False,
        "external_source_packet_loaded": bool(col.get("external_source_packet_loaded")) if isinstance(col, dict) else False,
        "web_search_attempted": bool(col.get("web_search_attempted")) if isinstance(col, dict) else False,
        "web_search_succeeded": bool(col.get("web_search_succeeded")) if isinstance(col, dict) else False,
        "web_search_result_count": int(col.get("web_search_result_count") or 0) if isinstance(col, dict) else 0,
        "external_source_count": int(col.get("external_source_count") or 0) if isinstance(col, dict) else 0,
        "seed_only": bool(col.get("seed_only")) if isinstance(col, dict) else False,
    }
    fm["citation_grounding_summary"] = {
        "raf": cg.get("relevance_aware_factuality_score"),
        "dfl": cg.get("deflection_rate_when_no_grounding"),
        "passed": cg.get("passed"),
        "requires_grounding": cg.get("requires_grounding"),
        "claims_total": cg.get("claims_total"),
        "claims_grounded": cg.get("claims_grounded"),
    }
    jw(rd / "feature-truth-matrix.json", fm)
    wave_ok = (rd / "graph/wave-plan.json").is_file()
    cg_ok = bool(cg.get("passed"))
    jw(
        rd / "final-answer-gate.json",
        minimal_valid(
            "final-answer-gate",
            overrides={
                "run_id": run_id,
                "passed": wave_ok and cg_ok,
                "status": "pass" if (wave_ok and cg_ok) else "fail",
                "checks": {
                    "wave_plan_materialized": wave_ok,
                    "citation_grounding_passed": cg_ok,
                    "driver": STANDALONE_DRIVER_ARTIFACT_TAG,
                },
            },
        ),
    )
    return cg
