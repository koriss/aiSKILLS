"""Validate ``research/research-plan.json`` against bundled schema (stdlib walker)."""
from __future__ import annotations

import json
from pathlib import Path

from runtime.util import skill_root
from validators.core.v19_stdlib_schema_walk import validate_instance


def load_research_plan_schema() -> dict:
    p = skill_root() / "contracts" / "research-plan-v1.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def collect_research_plan_errors(rd: Path) -> list[dict[str, str]]:
    rd = Path(rd)
    plan_path = rd / "research" / "research-plan.json"
    if not plan_path.is_file():
        return []
    try:
        doc = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [{"research_plan_json": str(e)}]
    if not isinstance(doc, dict):
        return [{"research_plan_shape": "root must be object"}]
    schema = load_research_plan_schema()
    pairs = validate_instance(doc, schema, root=schema, path="$", strict_additional=False)
    if not pairs:
        return []
    return [{"research_plan_schema": f"{c}: {m}"} for c, m in pairs]


def validate_plan_document(doc: object) -> list[tuple[str, str]]:
    if not isinstance(doc, dict):
        return [("RFO-PLAN", "root must be object")]
    schema = load_research_plan_schema()
    return validate_instance(doc, schema, root=schema, path="$", strict_additional=False)
