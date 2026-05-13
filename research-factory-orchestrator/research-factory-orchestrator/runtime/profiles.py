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

_DEFAULT = "dossier"


def _canonical_profile(name: str) -> str:
    return str(name or "").strip().lower()


def _path() -> Path:
    return Path(__file__).resolve().parent.parent / "contracts" / "run-profiles.json"


def load_profiles() -> dict[str, Any]:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        return {"profiles": {}, "default_profile": _DEFAULT}


def resolve(profile: str | None, *, entrypoint_default: str | None = None) -> tuple[str, dict[str, Any]]:
    """Resolve active profile. Unknown ``RFO_RUN_PROFILE`` env → ``ValueError`` (fail-closed).

    ``entrypoint_default`` (e.g. ``search-primary`` for standalone relay test harness) is used
    only when CLI profile and ``RFO_RUN_PROFILE`` are both unset; it does not change the
    global contract default (still ``dossier`` for worker/bridge).
    """
    contract = load_profiles()
    profiles = contract.get("profiles") or {}
    default = _canonical_profile(str(contract.get("default_profile") or _DEFAULT))
    env_raw = _canonical_profile(os.environ.get("RFO_RUN_PROFILE", ""))
    cli_raw = _canonical_profile((profile or "").strip())
    ed = _canonical_profile((entrypoint_default or "").strip()) if entrypoint_default else ""
    fallback = ed if ed and ed in profiles else default
    chosen = cli_raw or env_raw or fallback
    if chosen not in profiles:
        if env_raw and env_raw not in profiles:
            raise ValueError(f"unknown RFO_RUN_PROFILE={env_raw!r}; known={sorted(profiles)}")
        if cli_raw and cli_raw not in profiles:
            raise ValueError(f"unknown run profile (CLI)={cli_raw!r}; known={sorted(profiles)}")
        chosen = default
    return chosen, dict(profiles.get(chosen) or {})
