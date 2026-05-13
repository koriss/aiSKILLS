# ADR-021 — Research plan on disk + sequential relay (bridge)

## Status

Accepted (v19.4.x bridge).

## Context

The relay prefetch bridge (`scripts/run_rfo_with_web_search.py`) historically ran relay fanout before `allocate()`, so an early failure left no run directory for triage. Operators also need a versioned, machine-readable **research plan** (axes, waves, queries) separate from ad-hoc orchestrator trees.

## Decision

1. **Single `run_dir` per job:** the bridge calls `runtime.render.allocate` **first**, then `bootstrap_early_run_dir`, materializes `research/research-plan.json`, runs relay, and passes the same directory to the adapter via **`RFO_PREALLOCATED_RUN_DIR`** (`runtime/adapter_impl.py` skips a second `allocate` when set and validates path + `run-catalog-entry.json`).
2. **Plan contract:** `contracts/research-plan-v1.schema.json` with examples under `research/research-plan.json`. **`RFO_RESEARCH_PLAN_MODE`**: `off` (deterministic plan from template vectors, default for CI) or `llm_v1` (OpenAI-compatible planner envs under `RFO_RESEARCH_PLANNER_*`, one schema repair retry, then deterministic fallback).
3. **Execution remains sequential:** `llm_v1` only affects planning on disk; relay execution uses the same sequential merge semantics as today — either `fanout_relay_search` (`off`) or `fanout_relay_search_from_queries` (`llm_v1`) from `scripts/rfo_query_fanout.py` — not a multi-agent swarm (`docs/design/RFO-SEQUENTIAL-SEARCH-NO-MULTI-AGENT.md`).
4. **Wave graph gate:** the bridge writes **`graph/wave-plan.json`** early from the plan (`runtime/research_plan_planner.materialize_wave_plan`) so `wave_graph_gate` sees a real file before packaging; semantics of `passed` vs dossier depth remain documented in the repair plan.
5. **Validation boundary:** when `research/research-plan.json` declares `schema_version: research-plan-v1`, `runtime/validate_impl.py` (v19 path) runs `collect_research_plan_errors` after core validators pass. Scaffold-only runs (generic `pkg-generic-object` stub without that version) skip strict plan schema checks.

## Consequences

- `contracts/package-required-artifacts.json` lists `research/research-plan.json`; `ensure_pkg_required_paths` may create a generic stub on non-bridge runs — the plan validator ignores it unless `schema_version` matches.
- `collection-result.json` gains `research_plan_mode`, `research_plan_planner` (when applicable), and existing `relay_query_fanout` stats.

## Deferred (post-v1 hardening)

Explicitly **out of scope** for this ADR: durable `run_state.json` machine, per-phase metrics JSONL, relay checkpoint/resume, SIGTERM → `cancelled`, fuzz/property tests on merge, full SSRF policy for arbitrary URLs in plans, formal `stop_when` / evidence tier enforcement. Reserve nullable `evidence_policy` / `stop_when` in the schema for forward-compatible extensions.
