# ADR: RFO portable runs-root and host-owned paths

## Status

Accepted

## Context

RFO must run on hosts that do not use a fixed agent workspace layout. The repository therefore treats **runs-root** and relay bases as **operator-supplied**; `scripts/_rfo_path_guard.py` only blocks unsafe roots (e.g. `/tmp` without consent) and validates canonical skill path.

## Decision

- **Default allowed runs-roots** (in addition to `RFO_RUNS_ROOT` if set):
  - `$HOME/.openclaw/workspace/rfo-runs` (compatibility)
  - `$HOME/rfo-runs` (portable home-relative default)
- **Override:** set `RFO_RUNS_ROOT` to an absolute path to add another allowed root.
- **Portable hint text** in path-guard errors references `<SKILL_ROOT>` and `RFO_RUNS_ROOT`, not a single vendor workspace.
- **Container path mapping** for artifact handoff: `RFO_HOST_WORKSPACE_ROOT` and `RFO_CONTAINER_WORKSPACE_PREFIX` are both optional; if the host path is set, the container prefix must be set explicitly (no implicit OpenClaw default).

## Consequences

- OpenClaw-style deployments keep working when `~/.openclaw/workspace/rfo-runs` is used.
- Other environments can use `~/rfo-runs` or any tree under `RFO_RUNS_ROOT` without editing the skill.
