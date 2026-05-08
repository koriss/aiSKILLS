#!/usr/bin/env python3
"""Guard: seed-only / external-collection truth flags must be internally consistent.

Closes failure codes:
  * EXTERNAL-COLLECTION-MISREPORTED — sources present but every record is seed-only
    while ``external_web_search_executed=true``;
  * WEB-SEARCH-FLAG-FALSE-POSITIVE-NO-RESULTS — ``external_web_search_executed=true``
    while ``web_search_succeeded=false`` or ``web_search_result_count=0``;
  * SOURCE-PROVENANCE-CONFLATION — operator-supplied source packet conflated with
    live web search (collector reports both flags as the same value);
  * SEED-ONLY-MISREPORTED — feature-truth-matrix says ``external_collector=implemented_real``
    but ``collection_summary.seed_only=true``.

stdlib-only, fail-closed. Reads ``collection-result.json`` and ``feature-truth-matrix.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


VALIDATOR_ID = "validate_seed_only_truth"


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": VALIDATOR_ID,
                "schema_version": "v19.0",
                "passed": passed,
                "blocking": blocking,
                "issues": issues,
                "warnings": warnings,
                "summary": summary,
            },
            ensure_ascii=False,
        )
    )


def _load(p: Path):
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_parse_error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues: list[dict] = []
    warnings: list[dict] = []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    cr = _load(rd / "collection-result.json")
    matrix = _load(rd / "feature-truth-matrix.json")
    if not isinstance(cr, dict):
        issues.append({"code": "COLLECTION-RESULT-MISSING", "severity": "error", "detail": "collection-result.json missing"})
        _emit(False, True, issues, warnings, "no collection-result")
        return 1
    if "_parse_error" in cr:
        issues.append({"code": "COLLECTION-RESULT-PARSE-FAILED", "severity": "error", "detail": cr["_parse_error"]})
    web_ok = bool(cr.get("external_web_search_executed", False))
    succeeded = bool(cr.get("web_search_succeeded", False))
    rc = int(cr.get("web_search_result_count", 0) or 0)
    attempted = bool(cr.get("web_search_attempted", False))
    backend = cr.get("backend")
    seed_only = bool(cr.get("seed_only", True))
    packet_loaded = bool(cr.get("external_source_packet_loaded", False))
    if web_ok and not succeeded:
        issues.append({"code": "WEB-SEARCH-FLAG-FALSE-POSITIVE-NO-RESULTS", "severity": "error", "detail": "external_web_search_executed=true but web_search_succeeded=false"})
    if web_ok and rc <= 0:
        issues.append({"code": "WEB-SEARCH-FLAG-FALSE-POSITIVE-NO-RESULTS", "severity": "error", "detail": "external_web_search_executed=true but web_search_result_count=0"})
    if web_ok and not attempted:
        issues.append({"code": "WEB-SEARCH-FLAG-WITHOUT-ATTEMPT", "severity": "error", "detail": "external_web_search_executed=true but web_search_attempted=false"})
    if web_ok and backend in ("no_network", "no_seeds", "off"):
        issues.append({"code": "EXTERNAL-COLLECTION-MISREPORTED", "severity": "error", "detail": f"external_web_search_executed=true with backend={backend!r}"})
    if web_ok and packet_loaded and rc == 0:
        issues.append({"code": "SOURCE-PROVENANCE-CONFLATION", "severity": "error", "detail": "web search reported success but only source-packet provenance present"})
    src = (rd / "sources.json")
    n_sources = 0
    if src.is_file():
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("sources"), list):
                n_sources = len(data["sources"])
        except Exception as e:
            warnings.append({"code": "SOURCES-ROOT-PARSE-FAILED", "severity": "warning", "detail": str(e)})
    if web_ok and n_sources == 0:
        issues.append({"code": "EXTERNAL-COLLECTION-MISREPORTED", "severity": "error", "detail": "external_web_search_executed=true but sources.json contains 0 sources"})
    if seed_only and (web_ok or packet_loaded):
        issues.append({"code": "SEED-ONLY-FLAG-INCONSISTENT", "severity": "error", "detail": "seed_only=true but a real-source flag is set"})
    if isinstance(matrix, dict):
        feats = (matrix.get("features") or {}) if isinstance(matrix.get("features"), dict) else {}
        ec = feats.get("external_collector")
        if ec == "implemented_real" and seed_only:
            issues.append({"code": "SEED-ONLY-MISREPORTED", "severity": "error", "detail": "feature-truth-matrix claims external_collector=implemented_real but seed_only=true"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, "seed-only / web-search truth gate")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
