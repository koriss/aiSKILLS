"""Synthesize minimal JSON values from JSON Schema (structure-only, no domain literals in Python)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "core"


def schema_core_path(schema_name: str) -> Path:
    """Path to ``schemas/core/<name>.schema.json``."""
    return _SCHEMAS_DIR / f"{schema_name}.schema.json"


def load_core_schema(schema_name: str) -> dict[str, Any]:
    p = schema_core_path(schema_name)
    return json.loads(p.read_text(encoding="utf-8"))


def synth_value(sub: dict[str, Any], root: dict[str, Any]) -> Any:
    if "const" in sub:
        return sub["const"]
    if "enum" in sub and isinstance(sub["enum"], list) and sub["enum"]:
        return sub["enum"][0]
    t = sub.get("type")
    if t == "string":
        return ""
    if t == "integer":
        return 0
    if t == "number":
        return 0
    if t == "boolean":
        return False
    if t == "array":
        return []
    if t == "object" or ("properties" in sub and isinstance(sub.get("properties"), dict)):
        return synth_object(sub, root)
    if "oneOf" in sub and isinstance(sub.get("oneOf"), list):
        for br in sub["oneOf"]:
            if isinstance(br, dict):
                return synth_value(br, root)
    if "anyOf" in sub and isinstance(sub.get("anyOf"), list):
        for br in sub["anyOf"]:
            if isinstance(br, dict):
                return synth_value(br, root)
    return None


def synth_object(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    req = schema.get("required") if isinstance(schema.get("required"), list) else []
    for rk in req:
        if rk not in props or not isinstance(props[rk], dict):
            continue
        out[rk] = synth_value(props[rk], root)
    return out


def synth_from_json_schema(schema: dict[str, Any], overrides: Mapping[str, Any] | None = None) -> Any:
    """Return a minimal value for the root JSON Schema (object, array, string, etc.)."""
    if not isinstance(schema, dict):
        return None
    t = schema.get("type")
    if t == "object" or isinstance(schema.get("properties"), dict):
        base = synth_object(schema, schema)
        if overrides:
            merged = dict(base)
            merged.update(dict(overrides))
            return merged
        return base
    if t == "array":
        return []
    if t == "string":
        return synth_value({"type": "string"}, schema)
    if t == "integer":
        return 0
    if t == "number":
        return 0
    if t == "boolean":
        return False
    if "const" in schema:
        return schema["const"]
    if "enum" in schema and isinstance(schema.get("enum"), list) and schema["enum"]:
        return schema["enum"][0]
    if "oneOf" in schema and isinstance(schema.get("oneOf"), list):
        for br in schema["oneOf"]:
            if isinstance(br, dict):
                return synth_from_json_schema(br, overrides)
    if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
        for br in schema["anyOf"]:
            if isinstance(br, dict):
                return synth_from_json_schema(br, overrides)
    if schema.get("properties") or t == "object":
        return synth_object(schema, schema)
    return {}


def synth_from_core_schema_name(schema_name: str, overrides: Mapping[str, Any] | None = None) -> Any:
    """Load ``schemas/core/<name>.schema.json`` and synthesize."""
    return synth_from_json_schema(load_core_schema(schema_name), overrides)
