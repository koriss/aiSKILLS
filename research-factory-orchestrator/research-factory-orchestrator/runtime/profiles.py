"""Run-profile loader (RFO v19.2.0).

Single source of truth for profile policies (source_policy, delivery_policy,
active_validators). Reads ``contracts/run-profiles.json`` so JSON config and
runner code never drift (Phase 4C P1 PROFILE-VALIDATOR-DRIFT closure).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_DEFAULT = "mvr"
_KNOWN = ("mvr", "source-packet", "live-bridge", "full-rigor")


def _path() -> Path:
    return Path(__file__).resolve().parent.parent / "contracts" / "run-profiles.json"


def load_profiles() -> dict[str, Any]:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        return {"profiles": {}, "default_profile": _DEFAULT}


def resolve(profile: str | None) -> tuple[str, dict[str, Any]]:
    """Resolve active profile. Unknown ``RFO_RUN_PROFILE`` env → ``ValueError`` (fail-closed)."""
    contract = load_profiles()
    profiles = contract.get("profiles") or {}
    default = str(contract.get("default_profile") or _DEFAULT).strip().lower()
    env_raw = os.environ.get("RFO_RUN_PROFILE", "").strip().lower()
    cli_raw = (profile or "").strip().lower()
    chosen = cli_raw or env_raw or default
    if chosen not in profiles:
        if env_raw and env_raw not in profiles:
            raise ValueError(f"unknown RFO_RUN_PROFILE={env_raw!r}; known={sorted(profiles)}")
        if cli_raw and cli_raw not in profiles:
            raise ValueError(f"unknown run profile (CLI)={cli_raw!r}; known={sorted(profiles)}")
        chosen = default
    return chosen, dict(profiles.get(chosen) or {})
