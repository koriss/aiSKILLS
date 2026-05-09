"""Materialize missing ``PKG_REQUIRED`` paths from ``contracts/package-required-artifacts.json`` (schema-driven)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from runtime.schema_synth import load_core_schema, synth_from_json_schema
from runtime.util import jw, now, skill_root, tw


def package_contract_path() -> Path:
    return skill_root() / "contracts" / "package-required-artifacts.json"


def load_package_contract() -> dict[str, Any]:
    return json.loads(package_contract_path().read_text(encoding="utf-8"))


def _base_overrides(run_id: str, job_id: str, command_id: str) -> dict[str, Any]:
    ts = now()
    return {
        "run_id": run_id,
        "job_id": job_id,
        "command_id": command_id,
        "timestamp": ts,
        "created_at": ts,
        "started_at": ts,
    }


def ensure_pkg_required_paths(
    rd: Path,
    run_id: str,
    job_id: str,
    command_id: str,
    *,
    extra_overrides: Mapping[str, Any] | None = None,
) -> None:
    """Create any missing contract-listed artifacts under ``rd`` (never overwrite)."""
    rd = Path(rd)
    data = load_package_contract()
    arts = data.get("artifacts", [])
    ov = _base_overrides(run_id, job_id, command_id)
    if extra_overrides:
        ov = {**ov, **dict(extra_overrides)}
    for entry in arts:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("relpath")
        if not isinstance(rel, str) or not rel.strip():
            continue
        path = rd / rel
        if path.is_file():
            continue
        kind = (entry.get("kind") or "json").strip().lower()
        if kind == "json":
            cs = entry.get("core_schema") or "pkg-generic-object"
            schema = load_core_schema(str(cs))
            payload = synth_from_json_schema(schema, ov)
            jw(path, payload)
        elif kind == "jsonl":
            ls = entry.get("line_schema") or "pkg-jsonl-event"
            schema = load_core_schema(str(ls))
            line_ov = {**ov, "event_name": "pkg_scaffold"}
            line = synth_from_json_schema(schema, line_ov)
            tw(path, json.dumps(line, ensure_ascii=False) + "\n")
        elif kind == "text":
            cs = entry.get("core_schema") or "pkg-stub-empty-string"
            schema = load_core_schema(str(cs))
            payload = synth_from_json_schema(schema, {})
            if isinstance(payload, str):
                tw(path, payload)
            else:
                tw(path, "" if payload is None else str(payload))
        else:
            schema = load_core_schema("pkg-generic-object")
            jw(path, synth_from_json_schema(schema, ov))
