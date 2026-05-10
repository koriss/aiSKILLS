# ADR: RFO portable runs-root and host-owned paths

## Status

Accepted

## Context

RFO must run on hosts that do not use a fixed agent workspace layout. The repository therefore treats **runs-root** and relay bases as **operator-supplied**; `scripts/_rfo_path_guard.py` only blocks unsafe roots (e.g. `/tmp` without consent) and validates canonical skill path.

## Decision

- **Default allowed runs-roots** (in addition to `RFO_RUNS_ROOT` if set):
  - `$HOME/rfo-runs` (portable home-relative default)
  - `<host-workspace>/rfo-runs` (if provided by wrapper policy)
- **Override:** set `RFO_RUNS_ROOT` to an absolute path to add another allowed root.
- **Portable hint text** in path-guard errors references `<SKILL_ROOT>` and `RFO_RUNS_ROOT`, not a single vendor workspace.
- **Container path mapping** for artifact handoff: `RFO_HOST_WORKSPACE_ROOT` and `RFO_CONTAINER_WORKSPACE_PREFIX` are both optional; if the host path is set, the container prefix must be set explicitly (no implicit host-brand defaults).

## Consequences

- Host-managed deployments keep working when the wrapper supplies an explicit `RFO_RUNS_ROOT`.
- Other environments can use `~/rfo-runs` or any tree under `RFO_RUNS_ROOT` without editing the skill.
