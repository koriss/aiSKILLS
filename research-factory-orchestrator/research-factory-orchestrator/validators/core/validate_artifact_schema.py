#!/usr/bin/env python3
"""V1 — core artifact presence + JSON parse + schema_version v19.0 (stdlib hand-check).

Pre-run input artifacts (V1 does **not** require runner outputs):
  - sources.json or sources/sources.json
  - evidence-cards.json, claims-registry.json, final-answer-gate.json, delivery-manifest.json
  - contradictions-lite.json only when validation-profile-used.json (if present) sets
    options.require_full_contradiction_matrix == true

V1 does **not** require as input (avoid circular dependency with the runner):
  - validation-transcript.json — written only after V1–V6 complete
  - validation-profile-used.json — optional pre-run; typically written by run_core_validators.py before V1

Post-run transcript shape is validated separately (schema + check_validation_pass).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from v19_stdlib_schema_walk import validate_instance

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "core"

# (issue_tag, relative_file, schema_filename) — strict additionalProperties on artifacts.
_SCHEMA_CHECK: tuple[tuple[str, str, str], ...] = (
    ("SOURCES", "sources.json", "sources.schema.json"),
    ("EVIDENCE-CARDS", "evidence-cards.json", "evidence-cards.schema.json"),
    ("CLAIMS-REGISTRY", "claims-registry.json", "claims-registry.schema.json"),
    ("DELIVERY-MANIFEST", "delivery-manifest.json", "delivery-manifest.schema.json"),
    ("FINAL-ANSWER-GATE", "final-answer-gate.json", "final-answer-gate.schema.json"),
    ("CONTRADICTIONS-LITE", "contradictions-lite.json", "contradictions-lite.schema.json"),
)


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

    def _resolve_src() -> Path | None:
        s = rd / "sources.json"
        if s.is_file():
            return s
        s2 = rd / "sources" / "sources.json"
        return s2 if s2.is_file() else None

    for tag, rel_file, sch_name in _SCHEMA_CHECK:
        if rel_file == "sources.json":
            p = _resolve_src()
        else:
            p = rd / rel_file
        if not p or not p.is_file():
            continue
        so = _load(p)
        if so is None or (isinstance(so, dict) and so.get("_parse_error")):
            continue
        sch_path = SCHEMA_DIR / sch_name
        if not sch_path.is_file():
            issues.append(
                {
                    "code": "V1-SCHEMA-MISSING-SCHEMA-FILE",
                    "severity": "error",
                    "path": str(sch_path),
                    "detail": "schema file missing",
                    "artifact": rel_file,
                }
            )
            continue
        try:
            schema = json.loads(sch_path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(
                {
                    "code": "V1-SCHEMA-MISSING-SCHEMA-FILE",
                    "severity": "error",
                    "path": str(sch_path),
                    "detail": str(e),
                    "artifact": rel_file,
                }
            )
            continue
        if not isinstance(schema, dict):
            continue
        code = f"V1-SCHEMA-{tag}"
        for err_code, detail in validate_instance(so, schema, root=schema, path="$", issue_code=code, strict_additional=True):
            sev = "error"
            ic = err_code
            if err_code == "V1-SCHEMA-UNSUPPORTED-KEYWORD":
                ic = "V1-SCHEMA-UNSUPPORTED-KEYWORD"
            issues.append({"code": ic, "severity": sev, "path": rel_file, "detail": detail, "artifact": rel_file})
    blocking = any(i.get("severity") == "error" for i in issues)
    passed = not blocking
    _emit(passed, blocking, issues, warnings, "V1 artifact gate")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
