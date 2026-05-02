"""Publish / user-visible delivery policy (P0). Loaded from contracts/publish-policy.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Tuple


def load_publish_policy(skill_root: Path) -> dict[str, Any]:
    p = skill_root / "contracts" / "publish-policy.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def decide_publish_allowed(
    *,
    policy: Mapping[str, Any],
    run_mode: str,
    manual_fallback: bool,
    provider_pass: bool,
    any_failed: bool,
    external: bool,
    stub_only: bool,
) -> Tuple[bool, str]:
    """Returns (publish_allowed, reason_code)."""
    mode = (run_mode or "").strip()
    smoke_like = set(policy.get("smoke_like_modes") or ["smoke", "seed", "stub_test"])
    if policy.get("block_external_publish_on_smoke_like", True) and mode in smoke_like:
        return False, "blocked_smoke_like_mode"
    if policy.get("block_on_manual_fallback", True) and manual_fallback:
        return False, "manual_fallback_blocked"
    if policy.get("require_all_required_acks", True) and not provider_pass:
        return False, "provider_ack_incomplete"
    if policy.get("require_no_failed_acks", True) and any_failed:
        return False, "failed_ack_present"
    if stub_only and policy.get("require_external_delivery_for_user_publish", True):
        return False, "stub_only_no_external"
    if policy.get("require_external_delivery_for_user_publish", True) and not external:
        return False, "external_not_proven"
    if external:
        return True, "external_delivery_proven"
    return False, "policy_default_block"
