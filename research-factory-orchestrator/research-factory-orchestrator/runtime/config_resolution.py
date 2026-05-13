"""Single source of truth for bridge runs-root, workspace, relay, and preflight JSON.

**Canonical production** (default): ``--runs-root`` on argv is **required**; implicit
workspace / ``~/.openclaw/workspace/rfo-runs`` / ``~/rfo-runs`` resolution is **not**
used (see ``docs/plans/PLAN-rfo-agent-executable-single-behavior.md``).

**In-repo / CI fixture mode:** set ``RFO_RUN_EXECUTION_MODE=test_fixture`` (or
``fixture`` / ``ci``) to allow legacy resolution paths and tmp consent env keys
without treating them as canonical production.

``RFO_RUNS_ROOT`` remains deprecated compatibility when resolving inside fixture mode.

Canonical operator runs must not set forbidden env keys (see
``forbidden_canonical_env_keys``) unless ``RFO_RUN_EXECUTION_MODE`` selects fixture mode.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

RUNS_DIR_NAME = "rfo-runs"

_FORBIDDEN_EXACT = frozenset(
    {
        "RFO_SMOKE",
        "RFO_EXPERIMENT_BRIDGE",
        "RFO_ALLOW_LEGACY_ENTRYPOINT",
        "RFO_ALLOW_TMP_RUNS_ROOT",
        "RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT",
    }
)

# In ``RFO_RUN_EXECUTION_MODE=test_fixture`` only: recorded in effective-config but
# do not add ``forbidden_canonical_env`` to errors (path-guard / portable layout consent).
_RELAXED_IN_FIXTURE = frozenset({"RFO_ALLOW_TMP_RUNS_ROOT", "RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT"})


def _truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes")


def is_test_fixture_mode(env: Mapping[str, str] | os._Environ) -> bool:
    """True when harness explicitly opts into non-production resolution (CI / IDE in-repo)."""
    v = str(env.get("RFO_RUN_EXECUTION_MODE", "") or "").strip().lower()
    return v in ("test_fixture", "fixture", "ci")


def forbidden_canonical_env_keys(env: Mapping[str, str] | os._Environ) -> list[str]:
    """Env keys that must not be set for canonical operator / preflight runs."""
    out: list[str] = []
    for k in _FORBIDDEN_EXACT:
        if _truthy(str(env.get(k, "") or "")):
            out.append(k)
    for k in env:
        if k.startswith("RFO_ALLOW_LEGACY") and _truthy(str(env.get(k, "") or "")):
            if k not in out:
                out.append(k)
    return sorted(out)


def extract_argv_value(argv: list[str], flag: str) -> str | None:
    for i, tok in enumerate(argv):
        if tok == flag and i + 1 < len(argv):
            return argv[i + 1]
        prefix = f"{flag}="
        if tok.startswith(prefix):
            return tok.split("=", 1)[1]
    return None


def resolve_portable_default_runs_root() -> Path:
    """Portable default when no explicit workspace/runs-root (ADR-RFO_PORTABLE)."""
    extra = os.environ.get("RFO_RUNS_ROOT", "").strip()
    if extra:
        return Path(extra).expanduser().resolve(strict=False)
    home = Path.home()
    oc_root = home / ".openclaw" / "workspace" / RUNS_DIR_NAME
    ws = oc_root.parent
    portable = home / RUNS_DIR_NAME
    if oc_root.exists() or ws.exists():
        return oc_root
    return portable


def resolve_workspace_root(argv: list[str], env: Mapping[str, str] | os._Environ) -> tuple[Path | None, str]:
    raw = (extract_argv_value(argv, "--workspace-root") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve(strict=False), "argv:--workspace-root"
    ws = str(env.get("OPENCLAW_WORKSPACE_DIR", "") or "").strip()
    if ws:
        return Path(ws).expanduser().resolve(strict=False), "env:OPENCLAW_WORKSPACE_DIR"
    infer = Path.home() / ".openclaw" / "workspace"
    if infer.is_dir():
        return infer.resolve(strict=False), "infer:home.openclaw.workspace"
    return None, "missing"


def resolve_runs_root_for_bridge(
    argv: list[str],
    env: Mapping[str, str] | os._Environ,
) -> tuple[Path | None, str, list[str], list[str]]:
    """Return (runs_root_path, source_label, deprecated_inputs_used, config_errors)."""
    deprecated: list[str] = []
    errors: list[str] = []
    runs_argv = (extract_argv_value(argv, "--runs-root") or "").strip()
    if runs_argv:
        deprecated.append("argv_runs_root")
        p = Path(runs_argv).expanduser().resolve(strict=False)
        return p, "argv:--runs-root", deprecated, errors

    ws, ws_src = resolve_workspace_root(argv, env)
    if ws is not None:
        if ws_src.startswith("infer:"):
            deprecated.append("implicit_openclaw_home_workspace")
        return ws / RUNS_DIR_NAME, f"{ws_src}+{RUNS_DIR_NAME}", deprecated, errors

    extra = str(env.get("RFO_RUNS_ROOT", "") or "").strip()
    if extra:
        deprecated.append("env:RFO_RUNS_ROOT")
        return Path(extra).expanduser().resolve(strict=False), "env:RFO_RUNS_ROOT", deprecated, errors

    # Last-resort portable home (tests + bare checkout); always flagged.
    fb = resolve_portable_default_runs_root()
    deprecated.append("portable_home_fallback")
    return fb, "portable_default_chain", deprecated, errors


def resolve_relay_primary(cli_base: str, env: Mapping[str, str] | os._Environ) -> tuple[str | None, str]:
    c = (cli_base or "").strip()
    if c:
        return c.rstrip("/"), "argv:--web-search-json-api-base"
    e = str(env.get("RFO_WEB_SEARCH_JSON_API_BASE", "") or "").strip()
    if e:
        return e.rstrip("/"), "env:RFO_WEB_SEARCH_JSON_API_BASE"
    return None, "missing"


def secondary_relay_deprecated(env: Mapping[str, str] | os._Environ) -> str | None:
    s = str(env.get("RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE", "") or "").strip()
    return s.rstrip("/") if s else None


def relay_chain(cli_base: str, env: Mapping[str, str] | os._Environ) -> tuple[list[str], str | None, list[str]]:
    """Ordered unique relay bases (primary first), primary source, deprecated notes."""
    deprecated: list[str] = []
    primary, src = resolve_relay_primary(cli_base, env)
    sec = secondary_relay_deprecated(env)
    if sec:
        deprecated.append("env:RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE")
    seen: list[str] = []
    for raw in ((primary or "").strip(), sec or ""):
        if raw and raw not in seen:
            seen.append(raw.rstrip("/"))
    return seen, src, deprecated


def build_effective_config_snapshot(
    *,
    skill_root: Path,
    argv: list[str],
    env: Mapping[str, str] | os._Environ,
    cli_relay_base: str,
    profile: str,
    entrypoint: str,
) -> dict[str, Any]:
    fixture_mode = is_test_fixture_mode(env)
    forbidden = forbidden_canonical_env_keys(env)
    arg_runs = (extract_argv_value(argv, "--runs-root") or "").strip()

    if fixture_mode:
        runs_path, runs_src, dep_runs, errs = resolve_runs_root_for_bridge(argv, env)
    elif not arg_runs:
        runs_path, runs_src, dep_runs, errs = (
            None,
            "argv:--runs-root-missing",
            [],
            ["missing_required_argv_runs_root"],
        )
    else:
        runs_path, runs_src, dep_runs, errs = resolve_runs_root_for_bridge(argv, env)

    relays, relay_src, dep_relay = relay_chain(cli_relay_base, env)
    ws, ws_src = resolve_workspace_root(argv, env)
    deprecated = sorted(set(dep_runs + dep_relay))
    relay_primary = relays[0] if relays else None
    errs = list(errs)
    strict_forbidden = [k for k in forbidden if not (fixture_mode and k in _RELAXED_IN_FIXTURE)]
    if strict_forbidden:
        errs.append("forbidden_canonical_env")
    if not relays:
        errs.append("missing_relay")

    blocked_dependency: str | None = None
    if "missing_relay" in errs:
        blocked_dependency = "web_search_json_api_base"
    elif "missing_required_argv_runs_root" in errs:
        blocked_dependency = "runs_root_argv"

    if fixture_mode:
        run_execution_mode = "test_fixture"
    elif errs:
        run_execution_mode = "blocked_external_dependency"
    else:
        run_execution_mode = "canonical_production"

    production_research = run_execution_mode == "canonical_production"
    search_mode = "fixture_relay" if fixture_mode else "relay"

    snap: dict[str, Any] = {
        "schema": "rfo-effective-config-v1",
        "entrypoint": entrypoint,
        "profile": profile,
        "skill_root": str(skill_root.resolve()),
        "workspace_root": str(ws) if ws is not None else None,
        "workspace_root_source": ws_src,
        "runs_root": str(runs_path) if runs_path is not None else None,
        "runs_root_source": runs_src,
        "relay": relay_primary,
        "relay_source": relay_src,
        "relay_chain": relays,
        "deprecated_inputs_used": deprecated,
        "forbidden_inputs_present": forbidden,
        "canonical": not fixture_mode,
        "run_execution_mode": run_execution_mode,
        "production_research": production_research,
        "fixture_mode": fixture_mode,
        "search_mode": search_mode,
        "blocked_dependency": blocked_dependency,
        "errors": list(errs),
    }
    return snap


def log_startup_summary(snap: Mapping[str, Any]) -> None:
    """Stable stderr tags for gateway / Telegram log parsers."""
    import sys

    rem = snap.get("run_execution_mode") or "unknown"
    prod = snap.get("production_research")
    sys.stderr.write(
        f"[rfo-config] execution_mode={rem} production_research={prod} "
        f"entrypoint={snap.get('entrypoint')} "
        f"runs_root={snap.get('runs_root')} runs_root_source={snap.get('runs_root_source')} "
        f"relay={snap.get('relay')} relay_source={snap.get('relay_source')} "
        f"search_mode={snap.get('search_mode')}\n"
    )
    for d in snap.get("deprecated_inputs_used") or []:
        sys.stderr.write(f"[rfo-config-warning] deprecated_input={d}\n")
    if snap.get("fixture_mode"):
        for f in snap.get("forbidden_inputs_present") or []:
            sys.stderr.write(f"[rfo-config-fixture] non_production_env_detected={f}\n")
    else:
        for f in snap.get("forbidden_inputs_present") or []:
            sys.stderr.write(f"[rfo-config-error] forbidden_env={f}\n")
    for e in snap.get("errors") or []:
        sys.stderr.write(f"[rfo-config-error] {e}\n")
    sys.stderr.flush()


def build_effective_config_snapshot_source_packet_v2(
    *,
    skill_root: Path,
    argv: list[str],
    env: Mapping[str, str] | os._Environ,
    profile: str,
    entrypoint: str,
    source_packet_path: str,
    source_packet_sha256: str,
    packet_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Effective-config for ``scripts/rfo_execute.py`` source-packet path (no JSON relay)."""
    fixture_mode = is_test_fixture_mode(env)
    forbidden = forbidden_canonical_env_keys(env)
    arg_runs = (extract_argv_value(argv, "--runs-root") or "").strip()

    if fixture_mode:
        runs_path, runs_src, dep_runs, errs = resolve_runs_root_for_bridge(argv, env)
    elif not arg_runs:
        runs_path, runs_src, dep_runs, errs = (
            None,
            "argv:--runs-root-missing",
            [],
            ["missing_required_argv_runs_root"],
        )
    else:
        runs_path, runs_src, dep_runs, errs = resolve_runs_root_for_bridge(argv, env)

    ws, ws_src = resolve_workspace_root(argv, env)
    deprecated = sorted(set(dep_runs))
    errs = list(errs)
    strict_forbidden = [k for k in forbidden if not (fixture_mode and k in _RELAXED_IN_FIXTURE)]
    if strict_forbidden:
        errs.append("forbidden_canonical_env")

    blocked_dependency: str | None = None
    if "missing_required_argv_runs_root" in errs:
        blocked_dependency = "runs_root_argv"

    if fixture_mode:
        run_execution_mode = "test_fixture"
    elif errs:
        run_execution_mode = "blocked_external_dependency"
    else:
        run_execution_mode = "canonical_production"

    production_research = run_execution_mode == "canonical_production"
    meta = packet_meta or {}
    snap: dict[str, Any] = {
        "schema": "rfo-effective-config-v2",
        "entrypoint": entrypoint,
        "profile": profile,
        "skill_root": str(skill_root.resolve()),
        "workspace_root": str(ws) if ws is not None else None,
        "workspace_root_source": ws_src,
        "runs_root": str(runs_path) if runs_path is not None else None,
        "runs_root_source": runs_src,
        "relay": None,
        "relay_source": "none_agent_supplied_packet",
        "relay_chain": [],
        "deprecated_inputs_used": deprecated,
        "forbidden_inputs_present": forbidden,
        "canonical": not fixture_mode,
        "run_execution_mode": run_execution_mode,
        "production_research": production_research,
        "fixture_mode": fixture_mode,
        "search_mode": "agent_supplied_packet",
        "blocked_dependency": blocked_dependency,
        "errors": list(errs),
        "source_packet_path": source_packet_path,
        "source_packet_sha256": source_packet_sha256,
        "validation_profile": meta.get("validation_profile"),
        "execution_authenticity": meta.get("execution_authenticity"),
        "evidence_scope": meta.get("evidence_scope"),
        "collection_integrity": meta.get("collection_integrity"),
    }
    return snap
