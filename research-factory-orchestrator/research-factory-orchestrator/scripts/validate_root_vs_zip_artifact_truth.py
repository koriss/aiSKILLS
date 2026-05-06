#!/usr/bin/env python3
"""Guard: artifacts inside ``package/research-package.zip`` must match root-dir copies.

Closes:
  * ROOT-VS-ZIP-ARTIFACT-DRIFT — zip contains a different copy of an artifact
    (different sha256) than the on-disk root version. Validators that read root
    and downstream consumers that unzip then disagree.
  * ROOT-VS-ZIP-ARTIFACT-MISSING-IN-ZIP — required artifact present at root
    but missing from the package zip (or vice versa).

Compared artifacts (deterministic subset):
  - run.json
  - delivery-manifest.json
  - final-answer-gate.json
  - claims-registry.json
  - sources.json
  - evidence-cards.json
  - feature-truth-matrix.json
  - artifact-layout.json

stdlib-only, fail-closed. Skips silently with PASS+warning when the package zip
does not exist (e.g. before outbox finalization).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

VALIDATOR_ID = "validate_root_vs_zip_artifact_truth"
COMPARE = (
    "run.json",
    "delivery-manifest.json",
    "final-answer-gate.json",
    "claims-registry.json",
    "sources.json",
    "evidence-cards.json",
    "feature-truth-matrix.json",
    "artifact-layout.json",
)


def _emit(passed, blocking, issues, warnings, summary):
    print(json.dumps({"validator_id": VALIDATOR_ID, "schema_version": "v19.0", "passed": passed, "blocking": blocking, "issues": issues, "warnings": warnings, "summary": summary}, ensure_ascii=False))


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1048576), b""):
            h.update(c)
    return h.hexdigest()


def _sha_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    rd = Path(args.run_dir)
    issues, warnings = [], []
    if not rd.is_dir():
        _emit(False, True, [{"code": "missing_run_dir", "severity": "error", "detail": str(rd)}], [], "missing run dir")
        return 1
    pkg = rd / "package" / "research-package.zip"
    if not pkg.is_file():
        warnings.append({"code": "PACKAGE-ZIP-ABSENT", "severity": "warning", "detail": "package/research-package.zip not present yet"})
        _emit(True, False, issues, warnings, "no zip yet")
        return 0
    try:
        zf = zipfile.ZipFile(str(pkg), "r")
    except Exception as e:
        issues.append({"code": "PACKAGE-ZIP-UNREADABLE", "severity": "error", "detail": str(e)})
        _emit(False, True, issues, warnings, "zip unreadable")
        return 1
    names = set(zf.namelist())
    for rel in COMPARE:
        root_p = rd / rel
        in_root = root_p.is_file()
        in_zip = rel in names
        if in_root and not in_zip:
            issues.append({"code": "ROOT-VS-ZIP-ARTIFACT-MISSING-IN-ZIP", "severity": "error", "detail": f"root has {rel}, zip does not"})
            continue
        if in_zip and not in_root:
            issues.append({"code": "ROOT-VS-ZIP-ARTIFACT-MISSING-AT-ROOT", "severity": "error", "detail": f"zip has {rel}, root does not"})
            continue
        if in_root and in_zip:
            try:
                zip_bytes = zf.read(rel)
            except Exception as e:
                issues.append({"code": "ROOT-VS-ZIP-ARTIFACT-READ-FAILED", "severity": "error", "detail": f"{rel}: {e}"})
                continue
            if _sha(root_p) != _sha_bytes(zip_bytes):
                issues.append({"code": "ROOT-VS-ZIP-ARTIFACT-DRIFT", "severity": "error", "detail": f"sha256 mismatch for {rel}"})
    blocking = any(i.get("severity") == "error" for i in issues)
    _emit(not blocking, blocking, issues, warnings, f"root-vs-zip truth gate (compared={len(COMPARE)})")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
