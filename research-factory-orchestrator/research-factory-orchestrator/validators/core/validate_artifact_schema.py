#!/usr/bin/env python3
"""V1 — core artifact presence + JSON parse + schema_version v19.0 (stdlib hand-check)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _emit(passed: bool, blocking: bool, issues: list, warnings: list, summary: str) -> None:
    print(
        json.dumps(
            {
                "validator_id": "validate_artifact_schema",
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


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
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
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "path": str(rd), "detail": "not a directory", "artifact": ""}], [], "run_dir missing")
        return 1
    need = [
        ("evidence-cards.json", ("schema_version", "v19.0")),
        ("claims-registry.json", ("schema_version", "v19.0")),
        ("final-answer-gate.json", ("schema_version", "v19.0")),
        ("delivery-manifest.json", None),
        ("validation-transcript.json", None),
    ]
    src = rd / "sources.json"
    if not src.is_file():
        src = rd / "sources" / "sources.json"
    if not src.is_file():
        issues.append({"code": "missing_sources", "severity": "error", "path": "sources.json", "detail": "expected sources.json or sources/sources.json", "artifact": "sources"})
    else:
        so = _load(src)
        if so is None or isinstance(so, dict) and so.get("_parse_error"):
            issues.append({"code": "sources_parse", "severity": "error", "path": str(src), "detail": str(so), "artifact": "sources"})
        elif isinstance(so, dict) and so.get("schema_version") != "v19.0":
            issues.append({"code": "sources_schema_version", "severity": "error", "path": str(src), "detail": str(so.get("schema_version")), "artifact": "sources"})
    for rel, ver in need:
        p = rd / rel
        if not p.is_file():
            issues.append({"code": "missing_file", "severity": "error", "path": rel, "detail": "required core artifact missing", "artifact": rel})
            continue
        o = _load(p)
        if o is None or (isinstance(o, dict) and o.get("_parse_error")):
            issues.append({"code": "json_parse", "severity": "error", "path": rel, "detail": str(o), "artifact": rel})
            continue
        if ver and isinstance(o, dict) and o.get(ver[0]) != ver[1]:
            issues.append({"code": "schema_version", "severity": "error", "path": rel, "detail": f"want {ver[1]} got {o.get(ver[0])}", "artifact": rel})
    prof = rd / "validation-profile-used.json"
    if prof.is_file():
        po = _load(prof)
        opts = (po or {}).get("options") if isinstance(po, dict) else None
        if not isinstance(opts, dict):
            opts = {}
        if opts.get("require_full_contradiction_matrix") is True:
            cl = rd / "contradictions-lite.json"
            if not cl.is_file():
                issues.append({"code": "missing_contradictions_lite", "severity": "error", "path": "contradictions-lite.json", "detail": "profile requires file", "artifact": "contradictions-lite.json"})
    blocking = any(i.get("severity") == "error" for i in issues)
    passed = not blocking
    _emit(passed, blocking, issues, warnings, "V1 artifact gate")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
