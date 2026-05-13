"""Single source of truth for bridge runs-root, workspace, relay, and preflight JSON.

Contract **W** (workspace-first): ``runs_root`` defaults to
``{workspace_root}/rfo-runs`` where ``workspace_root`` comes from
``--workspace-root``, ``OPENCLAW_WORKSPACE_DIR``, or (deprecated infer)
``$HOME/.openclaw/workspace`` when that directory exists.

Explicit ``--runs-root`` remains supported for CI/machines (recorded as
deprecated in ``effective-config``). ``RFO_RUNS_ROOT`` is deprecated.

Canonical operator runs must not set forbidden env keys (see
``forbidden_canonical_env_keys``).
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
    }
)


def _truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes")


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
    forbidden = forbidden_canonical_env_keys(env)
    runs_path, runs_src, dep_runs, errs = resolve_runs_root_for_bridge(argv, env)
    relays, relay_src, dep_relay = relay_chain(cli_relay_base, env)
    ws, ws_src = resolve_workspace_root(argv, env)
    deprecated = sorted(set(dep_runs + dep_relay))
    relay_primary = relays[0] if relays else None
    errs = list(errs)
    if forbidden:
        errs.append("forbidden_canonical_env")
    if not relays:
        errs.append("missing_relay")
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
        "canonical": True,
        "errors": list(errs),
    }
    return snap


def log_startup_summary(snap: Mapping[str, Any]) -> None:
    """Stable stderr tags for gateway / Telegram log parsers."""
    import sys

    mode = "canonical"
    sys.stderr.write(
        f"[rfo-config] mode={mode} entrypoint={snap.get('entrypoint')} "
        f"runs_root={snap.get('runs_root')} runs_root_source={snap.get('runs_root_source')} "
        f"relay={snap.get('relay')} relay_source={snap.get('relay_source')}\n"
    )
    for d in snap.get("deprecated_inputs_used") or []:
        sys.stderr.write(f"[rfo-config-warning] deprecated_input={d}\n")
    for f in snap.get("forbidden_inputs_present") or []:
        sys.stderr.write(f"[rfo-config-error] forbidden_env={f}\n")
    for e in snap.get("errors") or []:
        sys.stderr.write(f"[rfo-config-error] {e}\n")
    sys.stderr.flush()
