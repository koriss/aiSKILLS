"""External-collection broker (RFO v19.2.0, stdlib-only).

Honest about truth flags. Closes:
  * EXTERNAL-COLLECTION-MISREPORTED — never sets ``external_web_search_executed=true``
    unless the backend actually returned results.
  * WEB-SEARCH-FLAG-FALSE-POSITIVE-NO-RESULTS — splits *attempted*, *succeeded*,
    and *result_count* so an empty/failed response cannot impersonate a real fetch.
  * SOURCE-PROVENANCE-CONFLATION — distinguishes ``external_source_packet_loaded``
    (operator-supplied bundle) from ``external_web_search_executed`` (live HTTP).
  * RFO_NO_NETWORK toggle — returns ``backend="no_network"`` decisively without
    attempting any sockets.

The actual web search is intentionally minimal: stdlib ``urllib.request`` HEAD
probe of operator-provided seed URLs (``RFO_SEED_URLS=...,...``). If no seed
URLs are provided, behaviour is ``backend="no_results"`` (honest empty), not a
silent ``stub_only`` masquerade.

Error appendix: every failure is also written to ``<run_dir>/runtime/errors.jsonl``
through ``runtime.error_log.append_error`` so validate_error_log_quality has
material to score against.
"""
from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

from runtime.error_log import append_error
from runtime.status import VERSION
from runtime.util import jw, now, sid


_USER_AGENT = (os.environ.get("RFO_WEB_SEARCH_USER_AGENT") or "").strip() or f"RFO/{VERSION}-collector"


def _seed_urls() -> list[str]:
    raw = os.environ.get("RFO_SEED_URLS", "").strip()
    if not raw:
        return []
    return [u.strip() for u in raw.split(",") if u.strip()]


def _max_sources() -> int:
    """Default derived from coverage contract minimum (Phase 4C P0-1 closure).

    Falls back to ``20`` if contract is missing so strict profiles remain
    reachable by default.
    """
    raw = os.environ.get("RFO_MAX_EXTERNAL_SOURCES")
    if raw and raw.isdigit():
        return max(1, int(raw))
    try:
        repo_root = Path(__file__).resolve().parent.parent
        contract = json.loads((repo_root / "contracts" / "collection-coverage-contract.json").read_text(encoding="utf-8"))
        return int(contract.get("minimum_independent_sources_default") or contract.get("minimum_independent_sources", 20))
    except Exception:
        return 20


def _probe(url: str, timeout: float) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT}, method="HEAD")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (operator-controlled URL)
            return {"ok": True, "status_code": int(resp.status), "headers": dict(resp.headers.items()), "elapsed_ms": int((time.time() - started) * 1000)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status_code": int(e.code), "error": "http_error", "detail": str(e.reason), "elapsed_ms": int((time.time() - started) * 1000)}
    except (urllib.error.URLError, socket.timeout, OSError) as e:
        return {"ok": False, "status_code": 0, "error": "network_error", "detail": str(e), "elapsed_ms": int((time.time() - started) * 1000)}


def collect(rd: Path, *, run_id: str, job_id: str, profile: str | None = None) -> dict:
    """Run the collection broker and return a summary.

    Always writes ``<rd>/collection-result.json`` and updates ``sources.json`` /
    ``sources/sources.json`` with truthful flags. Never raises — failures land in
    ``runtime/errors.jsonl``.
    """
    rd = Path(rd)
    no_network = os.environ.get("RFO_NO_NETWORK") == "1"
    external_mode = os.environ.get("RFO_EXTERNAL_COLLECTION", "off").lower()  # off | optional | required
    source_packet_path = os.environ.get("RFO_SOURCE_PACKET")
    seeds = _seed_urls()
    started_at = now()
    web_search_attempted = False
    web_search_succeeded = False
    web_search_result_count = 0
    external_web_search_executed = False
    external_source_packet_loaded = False
    backend = "off"
    backend_reason = ""
    collected_sources: list[dict] = []
    if source_packet_path and Path(source_packet_path).is_file():
        try:
            packet = json.loads(Path(source_packet_path).read_text(encoding="utf-8"))
            if isinstance(packet, dict) and isinstance(packet.get("sources"), list):
                external_source_packet_loaded = True
                packet_rows = [dict(s) for s in packet["sources"] if isinstance(s, dict)][: _max_sources()]
                # Derive citation_scope from verification_mode so packet-supplied snippet rows
                # cannot accidentally be marked citation_eligible (closes SNIPPET-CITATION-ELIGIBLE).
                for row in packet_rows:
                    vm = row.get("verification_mode")
                    if "citation_scope" not in row:
                        if vm == "snippet_only":
                            row["citation_scope"] = "snippet_only"
                        elif vm in {"raw_document", "primary_access"}:
                            row["citation_scope"] = "raw_document"
                        else:
                            row["citation_scope"] = "unknown"
                    if row.get("citation_scope") == "snippet_only":
                        row["citation_eligible"] = False
                    row.setdefault("fetch_method", "source_packet")
                collected_sources.extend(packet_rows)
        except Exception as e:
            append_error(rd, code="SOURCE-PACKET-PARSE-FAILED", severity="error", detail=str(e), context={"path": source_packet_path})
    if no_network:
        backend = "no_network"
        backend_reason = "RFO_NO_NETWORK=1"
        append_error(rd, code="EXTERNAL-COLLECTION-DISABLED", severity="warning", detail="RFO_NO_NETWORK=1 set; external collection skipped", context={"profile": profile, "external_mode": external_mode})
    elif external_source_packet_loaded:
        backend = "source_packet"
        backend_reason = "RFO_SOURCE_PACKET"
    elif not seeds:
        backend = "no_seeds"
        backend_reason = "RFO_SEED_URLS not set"
        append_error(rd, code="EXTERNAL-COLLECTION-NO-SEEDS", severity="warning", detail="RFO_SEED_URLS empty; collector cannot probe", context={"profile": profile, "external_mode": external_mode})
    else:
        backend = "stdlib_http_head"
        web_search_attempted = True
        timeout = float(os.environ.get("RFO_HTTP_TIMEOUT", "5.0"))
        for u in seeds[: _max_sources()]:
            res = _probe(u, timeout=timeout)
            if res.get("ok"):
                web_search_result_count += 1
                collected_sources.append(
                    {
                        "source_id": sid("SRC", u, run_id),
                        "title": u,
                        "canonical_origin_id": u,
                        "url": u,
                        "source_role": "unknown",
                        "access_level": "primary_access",
                        "interest_alignment": "unknown",
                        "verification_mode": "raw_document",
                        "independence": "unknown",
                        "citation_eligible": True,
                        "corroboration_type": "unknown",
                    }
                )
            else:
                append_error(
                    rd,
                    code="EXTERNAL-FETCH-FAILED",
                    severity="warning",
                    detail=res.get("detail") or res.get("error", "unknown"),
                    context={"url": u, "status_code": res.get("status_code"), "elapsed_ms": res.get("elapsed_ms")},
                )
        web_search_succeeded = web_search_result_count > 0
        external_web_search_executed = web_search_succeeded
        if not web_search_succeeded:
            backend_reason = "no_results"
            append_error(
                rd,
                code="EXTERNAL-COLLECTION-NO-RESULTS",
                severity="warning",
                detail="all seed URLs returned errors or empty responses",
                context={"profile": profile, "seed_count": len(seeds)},
            )
    if external_mode == "required" and not (external_web_search_executed or external_source_packet_loaded):
        # Hard fail surface for downstream guards (full-rigor / required profile).
        append_error(
            rd,
            code="RFO_EXTERNAL_COLLECTION_REQUIRED_BUT_NO_BACKEND",
            severity="error",
            detail=f"backend={backend} reason={backend_reason!r} web_search_executed={external_web_search_executed} packet_loaded={external_source_packet_loaded}",
            context={"profile": profile, "external_mode": external_mode},
        )
    completed_at = now()
    summary = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "job_id": job_id,
        "profile": profile,
        "backend": backend,
        "backend_reason": backend_reason,
        "external_mode": external_mode,
        "no_network": no_network,
        "started_at": started_at,
        "completed_at": completed_at,
        "external_source_packet_loaded": external_source_packet_loaded,
        "external_source_packet_path": source_packet_path or "",
        "web_search_attempted": web_search_attempted,
        "web_search_succeeded": web_search_succeeded,
        "web_search_result_count": web_search_result_count,
        "external_web_search_executed": external_web_search_executed,
        "external_source_count": len(collected_sources),
        "seed_only": not (external_web_search_executed or external_source_packet_loaded),
        "synthetic_count": 0,
        "max_sources_cap": _max_sources(),
        "seed_urls_provided": seeds,
    }
    jw(rd / "collection-result.json", summary)
    return _update_sources_with_collection(rd, summary, collected_sources)


def _update_sources_with_collection(rd: Path, summary: dict, collected_sources: list[dict]) -> dict:
    """Merge collected sources into the v19 root sources.json."""
    root = rd / "sources.json"
    base = {
        "schema_version": "v19.0",
        "sources": [],
    }
    if root.is_file():
        try:
            cur = json.loads(root.read_text(encoding="utf-8"))
            if isinstance(cur, dict) and isinstance(cur.get("sources"), list):
                base = cur
        except Exception as e:
            append_error(rd, code="SOURCES-ROOT-PARSE-FAILED", severity="warning", detail=str(e), context={"path": str(root)})
    seen_ids = {s.get("source_id") for s in base.get("sources", []) if isinstance(s, dict)}
    for s in collected_sources:
        if s.get("source_id") and s["source_id"] not in seen_ids:
            base["sources"].append(s)
            seen_ids.add(s["source_id"])
    if summary.get("seed_only") is True and not base.get("sources"):
        base["sources"].append(
            {
                "source_id": "stub:seed-only",
                "title": "Seed-only synthetic source",
                "canonical_origin_id": "stub:seed-only",
                "source_role": "unknown",
                "access_level": "unknown",
                "interest_alignment": "unknown",
                "verification_mode": "opinion",
                "independence": "unknown",
                "citation_eligible": False,
                "corroboration_type": "unknown",
            }
        )
        summary["synthetic_count"] = 1
    base["schema_version"] = "v19.0"
    jw(root, base)
    summary["root_sources_count_after"] = len(base["sources"])
    jw(rd / "collection-result.json", summary)
    return summary
