#!/usr/bin/env python3
"""F1: detect JSON Schema composition + additionalProperties:false merge hazards (draft-7/2020-12)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "schemas" / "core"


def _props_deep(node: object) -> set[str]:
    keys: set[str] = set()
    if not isinstance(node, dict):
        return keys
    props = node.get("properties")
    if isinstance(props, dict):
        keys.update(props.keys())
    for kw in ("oneOf", "anyOf", "allOf"):
        for br in node.get(kw) or []:
            if isinstance(br, dict):
                keys |= _props_deep(br)
    return keys


def _collect_composed_props(node: dict[str, object]) -> set[str]:
    cand: set[str] = set()
    for kw in ("oneOf", "anyOf", "allOf"):
        for br in node.get(kw) or []:
            if isinstance(br, dict):
                cand |= _props_deep(br)
    return cand


def _walk(node: object, path: str, rel_name: str, issues: list[dict[str, object]]) -> None:
    if not isinstance(node, dict):
        return
    comp = [k for k in ("oneOf", "anyOf", "allOf") if k in node]
    if comp and node.get("type") == "object":
        ap = node.get("additionalProperties", True)
        if ap is False:
            declared = set((node.get("properties") or {}).keys()) if isinstance(node.get("properties"), dict) else set()
            candidates = _collect_composed_props(node)
            missing = sorted(candidates - declared)
            if missing:
                issues.append(
                    {
                        "schema": rel_name,
                        "path": path or "$",
                        "composition": comp,
                        "additional_properties_false_at": path or "$",
                        "candidate_properties": missing,
                        "risk": "draft7_additionalProperties_does_not_see_composed_properties",
                    }
                )
    for k, v in node.items():
        npath = f"{path}.{k}" if path else f"$.{k}"
        _walk(v, npath, rel_name, issues)


def audit_file(path: Path) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [{"schema": path.name, "path": "$", "risk": "parse_error", "detail": str(e)}]
    _walk(data, "", path.name, issues)
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="Write composition-audit-report.json and exit 0 even if issues found")
    args = ap.parse_args()

    all_issues: list[dict[str, object]] = []
    scanned: list[str] = []
    if CORE.is_dir():
        for p in sorted(CORE.glob("*.json")):
            scanned.append(str(p.relative_to(ROOT)))
            all_issues.extend(audit_file(p))

    rep_path = ROOT / "composition-audit-report.json"
    rep_path.write_text(
        json.dumps({"status": "ok", "scanned": scanned, "issues": all_issues}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.report:
        print(json.dumps({"status": "report", "issues_count": len(all_issues), "report": str(rep_path)}, ensure_ascii=False))
        return 0

    if all_issues:
        print(json.dumps({"status": "fail", "issues": all_issues[:50], "issues_count": len(all_issues)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass", "issues_count": 0, "report": str(rep_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
