"""Optional JSON-relay reachability probe for RFO preflight (stdlib + shared relay client).

**Deprecation note (source-packet canonical):** new operator execute uses
``scripts/rfo_execute.py`` with an agent-assembled packet only; relay reachability
remains relevant for ``scripts/run_rfo_with_web_search.py`` preflight, not for
packet-only effective-config v2.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping


def _truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes")


def merge_relay_probe_into_snapshot(snap: dict[str, Any], env: Mapping[str, str] | os._Environ) -> None:
    """
    Mutates ``snap`` after ``build_effective_config_snapshot``: if primary relay is
    set and base config is otherwise valid, perform a minimal ``/search`` JSON
    request. On failure, append ``relay_unreachable`` and mark execution blocked.
    """
    if _truthy(str(env.get("RFO_SKIP_RELAY_PROBE", "") or "")):
        snap["relay_probe_skipped"] = True
        return

    errs = list(snap.get("errors") or [])
    if "missing_relay" in errs or "missing_required_argv_runs_root" in errs:
        return
    if "forbidden_canonical_env" in errs:
        return

    relay = (snap.get("relay") or "").strip()
    if not relay:
        return

    root = Path(__file__).resolve().parent.parent
    scripts = root / "scripts"
    sp = str(scripts)
    if sp not in sys.path:
        sys.path.insert(0, sp)

    from rfo_relay_search_helpers import relay_json_search  # noqa: PLC0415

    timeout = float(str(env.get("RFO_PREFLIGHT_RELAY_TIMEOUT", "") or "5.0") or "5.0")
    ua = (str(env.get("RFO_WEB_SEARCH_USER_AGENT") or "").strip() or "RFO/Preflight-Probe")

    try:
        _rows, meta = relay_json_search(
            relay,
            "rfo reachability probe",
            1,
            user_agent=ua,
            timeout=max(1.0, timeout),
        )
    except Exception as e:  # pragma: no cover - defensive
        ok, detail = False, f"exception:{e!r}"
        meta = {}
    else:
        # ``relay_json_search`` sets ``result_count`` only when JSON ``results`` was parsed.
        ok = "result_count" in meta
        if ok:
            detail = ""
        else:
            parts: list[str] = []
            for k in ("get_error", "post_error", "post_parse_failed", "post_no_results_key"):
                v = meta.get(k)
                if v:
                    parts.append(f"{k}={v!r}")
            detail = ";".join(parts) if parts else "relay_not_usable"

    if ok:
        snap["relay_reachable"] = True
        snap["relay_probe_error"] = None
        return

    snap["relay_reachable"] = False
    snap["relay_probe_error"] = detail
    if "relay_unreachable" not in errs:
        errs.append("relay_unreachable")
    snap["errors"] = errs
    snap["blocked_dependency"] = snap.get("blocked_dependency") or "web_search_json_api_base"
    snap["run_execution_mode"] = "blocked_external_dependency"
    snap["production_research"] = False
