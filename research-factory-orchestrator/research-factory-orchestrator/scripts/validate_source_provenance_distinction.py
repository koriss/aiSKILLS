#!/usr/bin/env python3
"""Guard: source-packet sources must NOT be reported as live-web-search sources.

Closes:
  * SOURCE-PROVENANCE-CONFLATION — collection-result.json reports
    ``external_web_search_executed=true`` while the only real source provenance
    is an operator-supplied ``RFO_SOURCE_PACKET`` (no live HTTP succeeded).
  * SNIPPET-CITATION-ELIGIBLE-WITHOUT-RAW — sources marked
    ``citation_eligible=true`` and ``verification_mode="snippet_only"`` simultaneously.
  * SOURCE-RECORD-MISSING-PROVENANCE-FIELDS — required v19 source fields
    (``canonical_origin_id``, ``source_role``, ``access_level``, ``verification_mode``,
    ``citation_eligible``) absent.

stdlib-only, fail-closed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALIDATOR_ID = "validate_source_provenance_distinction"
REQ_FIELDS = ("canonical_origin_id", "source_role", "access_level", "verification_mode", "citation_eligible")


def _emit(passed, blocking, issues, warnings, summary):
    print(json.dumps({"validator_id": VALIDATOR_ID, "schema_version": "v19.0", "passed": passed, "blocking": blocking, "issues": issues, "warnings": warnings, "summary": summary}, ensure_ascii=False))


def _load(p):
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
    issues, warnings = [], []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    cr = _load(rd / "collection-result.json") or {}
    src = _load(rd / "sources.json") or {}
    web_executed = bool(cr.get("external_web_search_executed", False))
    packet_loaded = bool(cr.get("external_source_packet_loaded", False))
    web_count = int(cr.get("web_search_result_count", 0) or 0)
    if web_executed and packet_loaded and web_count == 0:
        issues.append({"code": "SOURCE-PROVENANCE-CONFLATION", "severity": "error", "detail": "web search reported true with 0 result count while packet was loaded"})
    sources = src.get("sources") if isinstance(src, dict) else []
    for i, s in enumerate(sources or []):
        if not isinstance(s, dict):
            issues.append({"code": "SOURCE-RECORD-NOT-OBJECT", "severity": "error", "detail": f"sources[{i}] not an object"})
            continue
        missing = [f for f in REQ_FIELDS if f not in s]
        if missing:
            issues.append({"code": "SOURCE-RECORD-MISSING-PROVENANCE-FIELDS", "severity": "error", "detail": f"sources[{i}] missing={missing}"})
        vm = s.get("verification_mode")
        ce = s.get("citation_eligible")
        if vm == "snippet_only" and ce is True:
            issues.append({"code": "SNIPPET-CITATION-ELIGIBLE-WITHOUT-RAW", "severity": "error", "detail": f"sources[{i}] verification_mode=snippet_only with citation_eligible=true"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"source provenance gate (sources={len(sources or [])})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
