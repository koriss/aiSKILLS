# PR-0 — Vertical feasibility proof (source-packet + artifact pipeline)

## Goal

Prove that an **agent-written `source-packet-v1`** can drive the **existing** RFO artifact pipeline (adapter/worker/render/validators) **without** relay-runtime fields appearing in machine JSON, **or** document precise blockers for PR-1.

## Outcome (this repo state)

**Green for PR-0 scope:** `runtime/source_packet_run.py` loads bridge helpers from `scripts/run_rfo_with_web_search.py`, builds **`rfo-effective-config-v2`** via `runtime/config_resolution.build_effective_config_snapshot_source_packet_v2`, allocates run-dir, runs adapter + worker loop, merges postrun policy (bootstrap thresholds, snippet-heavy web → `final_verdict_allowed: false`, manual `evidence_scope` handling), and emits handoff.

**Worker dependencies (adapter boundary):** same subprocess contract as relay path: `interface_runtime_adapter` + `runtime_job_worker` expectations unchanged; packet supplies `collection-result` / sources in the shape the worker already accepts after bridge bootstrap.

**Required adapter fields (minimal):** `topic`, `created_at`, `profile` (from packet only in canonical path), `collection_methods`, `sources` / `collection-result` per `source-packet-v1` schema.

**Blockers (none blocking PR-1 vertical slice):** full production validator bar deferred to PR-1 (`run_core_validators` full pass). PR-0 allows bootstrap profile + documented gaps.

**Exact files touched for PR-1+** (reference): `scripts/rfo_execute.py`, `scripts/rfo_validate_source_packet.py`, `scripts/assert_no_relay_semantics.py`, `runtime/source_packet_run.py`, `runtime/config_resolution.py`, `runtime/canonical_env_guard.py`, `contracts/source-packet-v1.schema.json`, `contracts/rfo-effective-config-v2.schema.json`, `contracts/supported-skill-actions-v2.json`, `tests/test_rfo_execute_source_packet_contract.py`, `docs/runtime-paths.md`, `docs/adr/ADR-023-source-packet-canonical-execute.md`.

## Claims registry

Minimal **claims** / provenance hooks are applied in `source_packet_run` (patch pass); a fuller machine-readable registry is optional follow-up if product requires it — not a PR-0 gate.

## assert_no_relay

- **Strict:** JSON files under `run_dir` scanned for forbidden relay **runtime** keys (not the substring `web_search` in method names).
- **Soft:** optional `--soft-text` for `report/` / `chat/` phrase heuristics.

## Human report

Primary dossier text remains **`report/full-report.md`**; HTML is derived when the pipeline runs `render_all` — **one** human-readable spine, not two mandatory artifacts.
