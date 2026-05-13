"""Guardrails for ``scripts/rfo_execute.py`` source-packet canonical execute (stdlib-only)."""
from __future__ import annotations

import os
from typing import Mapping

# Operator must not steer canonical execute via these (profile/task/runs/relay come from argv + packet).
_FORBIDDEN_SEMANTIC = frozenset(
    {
        "RFO_SOURCE_PACKET",
        "RFO_RUNS_ROOT",
        "RFO_WEB_SEARCH_JSON_API_BASE",
        "RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE",
        "RFO_SMOKE",
        "RFO_EXPERIMENT_BRIDGE",
        "RFO_ALLOW_LEGACY_ENTRYPOINT",
        "RFO_RUN_PROFILE",
        "RFO_PREALLOCATED_RUN_DIR",
    }
)


def forbidden_semantic_rfo_env(env: Mapping[str, str] | os._Environ) -> list[str]:
    """Return sorted env keys that must not influence canonical source-packet execute."""
    bad: list[str] = []
    for k, v in env.items():
        if not k.startswith("RFO_"):
            continue
        if not str(v or "").strip():
            continue
        if k in _FORBIDDEN_SEMANTIC:
            bad.append(k)
            continue
        if k.startswith("RFO_ALLOW_LEGACY"):
            bad.append(k)
    return sorted(set(bad))
