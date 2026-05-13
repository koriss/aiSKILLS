# RFO_* environment classification

Normative narrative: `docs/plans/PLAN-rfo-agent-executable-single-behavior.md`.  
Effective-config snapshot records **which** inputs applied (`runs_root_source`, `relay_source`, `deprecated_inputs_used`, `forbidden_inputs_present`).

## Source-packet canonical execute (`scripts/rfo_execute.py`)

| Rule | Detail |
|------|--------|
| Inputs | **Argv:** `--runs-root` (required), optional `--source-packet`, optional `--allow-stale-packet`. **Packet JSON:** `topic`, `created_at`, `profile`, `sources`, … (`contracts/source-packet-v1.schema.json`). |
| Forbidden semantic `RFO_*` | Any non-empty value for keys listed in `runtime/canonical_env_guard.py` (including `RFO_RUN_PROFILE`, `RFO_SOURCE_PACKET`, relay bases, smoke/bridge flags) → exit **2**. Profile is **only** from the packet. |
| Harmless internal | Tunables such as `RFO_HTTP_TIMEOUT*`, `RFO_ALLOW_TMP_RUNS_ROOT` in fixture mode, etc., remain as in `docs/runtime-paths.md`. |
| `RFO_EFFECTIVE_ENTRYPOINT` | Set by **`rfo_execute.py`** before the inner pipeline so snapshots show `scripts/rfo_execute.py`. Do not export manually. |

## Canonical production (default, relay bridge)

| Variable | Role |
|----------|------|
| *(none required as env)* | Primary production inputs are **argv**: `--runs-root`, `--web-search-json-api-base`, `--task`, `--profile`. |

## Deprecated compatibility (still read; appears in `deprecated_inputs_used`)

| Variable | Effect |
|----------|--------|
| `RFO_RUNS_ROOT` | Runs root when `--runs-root` omitted **only** in `RFO_RUN_EXECUTION_MODE=test_fixture` resolution paths; in canonical production, `--runs-root` argv is required. |
| `RFO_WEB_SEARCH_JSON_API_BASE` | Relay when `--web-search-json-api-base` omitted. |
| `RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE` | Secondary relay; deprecated, not a second product path. |

## Forbidden in canonical (strict; preflight / run fails with `forbidden_canonical_env`)

| Variable |
|----------|
| `RFO_SMOKE` |
| `RFO_EXPERIMENT_BRIDGE` |
| `RFO_ALLOW_LEGACY_ENTRYPOINT` |
| `RFO_ALLOW_LEGACY*` (any extra legacy allow flags) |

## Relaxed only in `RFO_RUN_EXECUTION_MODE=test_fixture|fixture|ci`

Recorded in `forbidden_inputs_present` but **do not** add `forbidden_canonical_env` to errors:

| Variable | Why |
|----------|-----|
| `RFO_ALLOW_TMP_RUNS_ROOT` | Consent for `_rfo_path_guard` when `--runs-root` is under `/tmp`. |
| `RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT` | Portable checkout / symlink layouts for CI. |

## Execution mode harness

| Variable | Values |
|----------|--------|
| `RFO_RUN_EXECUTION_MODE` | `test_fixture`, `fixture`, or `ci` → `effective-config.run_execution_mode=test_fixture`, `fixture_mode=true`, `production_research=false`. Omit for canonical. |

## Internal tuning (not operator contract)

Examples: `RFO_HTTP_TIMEOUT*`, `RFO_BRIDGE_*`, `RFO_WIKIPEDIA_HEURISTIC`, `RFO_RESEARCH_PLAN_MODE`, `RFO_WEB_SEARCH_USER_AGENT`, worker lease TTLs — see `docs/runtime-paths.md` and profile JSON.

| Variable | Effect |
|----------|--------|
| `RFO_PREFLIGHT_RELAY_TIMEOUT` | Seconds for the JSON `/search` reachability probe (default **5.0**). |
| `RFO_SKIP_RELAY_PROBE` | When truthy, skips the probe (tests / special harness only; **not** for production triage). |
| `RFO_EFFECTIVE_ENTRYPOINT` | Set by the active entrypoint (`run_rfo_with_web_search.py` or the inner pipeline after `rfo_execute.py` resolves) so `effective-config.entrypoint` matches the binary on the audit trail; do not export manually to spoof audits. |
