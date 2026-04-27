# Internal Compiler Protocol

## Purpose
Emit a **runnable** runtime: contracts, state, queue model, policies, and empty/seed artifacts. Compilation finishes in state `runtime_compiled` and must be followed by execution (unless mode is `COMPILE_ONLY`).

## Outputs (minimum)
- `runtime-contract.json` — task metadata, execution mode, thresholds, global FSM anchor, security flags.
- `runtime-state.json` — `current_global_stage`, `current_item_id`, loop counters, blockers.
- `queue.json` — items for multi-item work; single item if lightweight.
- `artifact-manifest.json` — every tracked file, role, validation timestamp.
- `tool-registry.json` — seeds; executor fills `available` after discovery.
- `items/<item_slug>/` — per-item chain: sources, evidence, claims, drafts, fact-check, citation, audit, evaluation.
- `logs/trace.jsonl`, `logs/activity-history.html` — created if missing.

## Rules
- Idempotent: re-run compile may update contract version and `updated_at`; must not wipe `final` without `FORCE_REBUILD` + user intent.
- Never mark user work `delivered` at end of compile.
