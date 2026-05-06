"""Collection coverage reconciler (RFO v19.2.0).

Decouples ``collection_completed`` from ``source_coverage_passed``. Closes
COVERAGE-DECOUPLE-MISSING and COLLECTION-COMPLETED-WITHOUT-SOURCES.

Writes ``<run_dir>/collection-coverage-result.json`` with explicit fields:
  * ``minimum_independent_sources`` — threshold from profile
  * ``observed_independent_sources`` — count of unique source records
  * ``source_coverage_passed`` — bool, threshold-aware
  * ``collection_completed`` — bool, executor-aware (work units terminal AND
    collector ran), independent of coverage
  * ``passed`` — overall gate, equal to ``source_coverage_passed`` when the
    profile requires it, otherwise the disclosure-only honesty layer.
"""
from __future__ import annotations

import json
from pathlib import Path

from runtime.profiles import resolve as _resolve_profile
from runtime.util import jw, jr, now


def reconcile(rd: Path, *, run_id: str, job_id: str, profile: str | None) -> dict:
    rd = Path(rd)
    name, policy = _resolve_profile(profile)
    src_pol = policy.get("source_policy") or {}
    minimum = int(src_pol.get("minimum_independent_sources", 0) or 0)
    cr = jr(rd / "collection-result.json", {})
    summary = jr(rd / "work-queue" / "execution-summary.json", {})
    sources_root_path = rd / "sources.json"
    n_unique = 0
    if sources_root_path.is_file():
        try:
            data = json.loads(sources_root_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("sources"), list):
                seen = set()
                for s in data["sources"]:
                    if isinstance(s, dict) and isinstance(s.get("source_id"), str):
                        seen.add(s["source_id"])
                n_unique = len(seen)
        except Exception:
            n_unique = 0
    collection_completed = (
        bool(summary.get("total_terminal") == summary.get("total_planned") and (summary.get("total_planned") or 0) > 0)
        and bool(cr)
    )
    source_coverage_passed = n_unique >= minimum if minimum > 0 else True
    requires_external = bool(src_pol.get("external_collection_required", False))
    requires_web = bool(src_pol.get("web_search_required", False))
    requires_packet = bool(src_pol.get("source_packet_required", False))
    web_executed = bool(cr.get("external_web_search_executed", False))
    packet_loaded = bool(cr.get("external_source_packet_loaded", False))
    profile_requires_real = requires_external or minimum > 0 or requires_web or requires_packet
    passed = True
    failure_reasons: list[str] = []
    if profile_requires_real and not source_coverage_passed:
        passed = False
        failure_reasons.append("source_coverage_below_threshold")
    if requires_web and not web_executed:
        passed = False
        failure_reasons.append("web_search_required_not_executed")
    if requires_packet and not packet_loaded:
        passed = False
        failure_reasons.append("source_packet_required_not_loaded")
    if requires_external and not (web_executed or packet_loaded):
        passed = False
        failure_reasons.append("external_collection_required_no_backend")
    out = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "job_id": job_id,
        "profile": name,
        "minimum_independent_sources": minimum,
        "observed_independent_sources": n_unique,
        "source_coverage_passed": source_coverage_passed,
        "collection_completed": collection_completed,
        "external_web_search_executed": web_executed,
        "external_source_packet_loaded": packet_loaded,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "evaluated_at": now(),
    }
    jw(rd / "collection-coverage-result.json", out)
    return out
