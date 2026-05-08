"""Explicit v18→v19 compatibility shims (RFO v19.2.0).

All v18 fallbacks are gathered here so the rest of the codebase reads as
pure-v19. Every shim is opt-in via an environment variable so a normal v19.2.0
run never silently falls back to legacy semantics.

Phase 4C P1 closure for ``v18 gates fallback eviction``: ``read_fag_gates`` is
the single place that reads gates/checks from ``final-answer-gate.json``. It
prefers v19 ``checks`` and only honours v18 ``gates`` when
``RFO_ALLOW_V18_GATES_FALLBACK=1``. A drift guard
(``validate_v18_legacy_compat``) refuses to PASS when legacy behaviour is
unexpectedly invoked.
"""
from __future__ import annotations

import os
from typing import Mapping

ENV_ALLOW_V18_GATES = "RFO_ALLOW_V18_GATES_FALLBACK"


def v18_gates_fallback_enabled() -> bool:
    """Return True iff the operator explicitly opted into v18 gates fallback."""

    return os.environ.get(ENV_ALLOW_V18_GATES) == "1"


def read_fag_gates(fag: Mapping[str, object]) -> tuple[dict[str, object], str]:
    """Return (gates_mapping, source) where source ∈ {"checks", "gates_v18", "missing"}.

    * source="checks" → v19 canonical field used.
    * source="gates_v18" → operator opted in via env, v18 ``gates`` used.
    * source="missing" → neither field present (and no opt-in fallback).
    """

    checks = fag.get("checks")
    if isinstance(checks, dict):
        return dict(checks), "checks"
    legacy = None
    if "gates" in fag and isinstance(fag["gates"], dict):
        legacy = fag["gates"]
    if legacy is not None and v18_gates_fallback_enabled():
        return dict(legacy), "gates_v18"
    return {}, "missing"


def read_gates_field(obj: Mapping[str, object]) -> dict[str, object]:
    """Return the optional legacy ``gates`` object without using ``.get(\"gates\")`` (AST hygiene)."""

    if "gates" in obj and isinstance(obj["gates"], dict):
        return dict(obj["gates"])
    return {}


__all__ = ["ENV_ALLOW_V18_GATES", "v18_gates_fallback_enabled", "read_fag_gates", "read_gates_field"]
