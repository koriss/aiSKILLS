# Changelog

## 19.4.11 — 2026-05-10

- **Command router:** `contracts/command-router-contract.json` maps native slash commands to **`scripts/run_rfo_with_web_search.py`** (JSON relay prefetch); **`scripts/rfo_execute.py`** remains source-packet-only canonical execute (`validate_command_router_mapping.py` updated).
- **Contracts:** `contracts/entrypoint-contract.json` adds **`native_relay_bridge_entrypoint`** alongside **`canonical_operator_research_entrypoint`**.
- **Validators:** `scripts/validate_docs_archival_markers.py` + hook from `validate_skill.py` (subtree `ARCHIVAL_CONTEXT_ONLY` policy).
- **`assert_no_relay_semantics.py`:** stricter relay-runtime detection (`relay_chain` non-empty, non-null `relay` URL, `relay_prefetch_bridge: true`, disallowed `relay_source`).
- **Fixtures / templates:** `tests/fixtures/source_packets/blocked_packet.json`; `templates/source-packet.bootstrap.example.json` for `--template-mode` checks.
- **Docs:** `docs/runtime-paths.md` (preflight + adapter policy use relay bridge, not `rfo_execute` legacy argv); `docs/rfo-env-classification.md` (source-packet execute section); `contracts/run-profiles.json` description alignment.
- **Anti-regression:** `scripts/validate_source_packet_contract_bundle.py` (fixtures + `templates/source-packet*.json` via `rfo_validate_source_packet.py`); invoked from `validate_skill.py`; `tests/__pycache__` stripped in the same gate as other bytecode dirs.
- **SKILL frontmatter:** `native_slash_relay_bridge` + `canonical_source_packet_execute`; explicit copy-paste subsection for the two packet transports; slash disclaimer that host owns packet + bridge choice.
- **Relay reachability:** `runtime/relay_reachability.py` module docstring — bridge-preflight only, not packet canonical (ADR-023 cross-link).

## 19.4.x — bridge + compute-only boundary

### 19.4.10 — 2026-05-10

- **Preflight relay probe:** `runtime/relay_reachability.py` — after config snapshot, minimal JSON `/search` via `relay_json_search`; on failure `relay_unreachable`, `blocked_dependency=web_search_json_api_base`, exit **2**; `RFO_SKIP_RELAY_PROBE` / `RFO_PREFLIGHT_RELAY_TIMEOUT` for harness only (ADR-022).
- **Effective-config entrypoint:** `scripts/rfo_execute.py` sets `RFO_EFFECTIVE_ENTRYPOINT` so stdout JSON shows **`scripts/rfo_execute.py`** for the **packet execute** façade (19.4.11: native slash / default production depth still flows through **`scripts/run_rfo_with_web_search.py`** per command-router).
- **Tests:** `test_bridge_cli_integration` uses local HTTP stub for successful preflight; new unreachable-relay case on closed port.
- **Docs:** `docs/runtime-paths.md`, `docs/rfo-env-classification.md`, `docs/adr/ADR-019-single-dossier-funnel.md` (consequences bullet), **ADR-022**; `PLAN-rfo-agent-executable-single-behavior.md` acceptance rows closed.

### 19.4.9 — 2026-05-10

- **Agent-executable contract:** `runtime/config_resolution.py` — canonical production requires argv `--runs-root`; `RFO_RUN_EXECUTION_MODE=test_fixture|fixture|ci` for in-repo harness; `run_execution_mode`, `production_research`, `fixture_mode`, `search_mode`, `blocked_dependency` on `rfo-effective-config-v1`; relaxed fixture handling for `RFO_ALLOW_TMP_RUNS_ROOT` / `RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT` only in fixture mode; startup stderr summary includes execution mode.
- **Contracts:** `contracts/rfo-effective-config-v1.schema.json` extended; `scripts/validate_agent_executable_doc_grep.py` + hook from `validate_skill.py`.
- **Docs:** `docs/plans/PLAN-rfo-agent-executable-single-behavior.md`, `docs/rfo-env-classification.md`; SKILL / SKILL-core / runtime-paths aligned; grave marker `run_rfo_full_research.py` message lists `--runs-root`.
- **Tests:** bridge integration tests set fixture mode for `/tmp` runs; `test_effective_config_schema_contract` covers missing argv runs-root and fixture snapshot.

### 19.4.8 — 2026-05-10

- **MD-first dossier:** `runtime/report_inputs.py` centralizes run-dir inputs; `runtime/report_md.py` writes **`report/full-report.md`**; `runtime/report_html.py` derives **`report/full-report.html`** only from that Markdown (`markdown` when available, else escaped `<pre>` fallback). `render_all` and `scripts/rfo_render.py canonical` follow MD → HTML; embedded JSON proof blocks remain in the HTML shell for validators.
- **Contracts / gates:** `report/full-report.md` is required in package layout and worker post-render checks; `content_gate` treats non-trivial MD as primary; HTML presence tracked as derivative.
- **Tests:** `tests/test_report_md_first_pipeline.py`.
- **Docs:** `docs/runtime-paths.md` (canonical files section); `docs/operator/rfo-llm-pipeline-checkpoints.md` (Layer A / B for LLM-assisted operators).
- **Host deploy (opt-openclaw):** rsync this package to the host skill tree only when the operator confirms the target instance; example:  
  `rsync -a --delete /home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/ /opt/openclaw/data/workspace/skills/research-factory-orchestrator/`  
  then `docker compose restart gateway` from that stack’s compose directory; smoke `/research_factory_orchestrator` per gateway runbook.

### 19.4.7 — 2026-05-10

- **Host / IDE agents:** `runtime/research_bridge_bootstrap.py` now materializes **`agent-operating-log.md`** at the root of each allocated **`run_dir`** (same path as `result-manifest.json`) so append-only step logs do not rely on guessed `rfo-runs/runs/<slug>/` trees.
- **SKILL.md / runtime-paths / gateway notes:** strict “resolve `run_dir` from handoff only” sequence; substance-first answers from **`report/full-report.html`**; **`propaganda-io`** profile only on explicit user ask; prohibition on parallel invented log paths.

### 19.4.6 — 2026-05-14

- Patch release: semver +0.0.1 (`runtime/version.json`, SKILL metadata, `contracts/run-profiles.json`, compatibility matrix).
- **Single-behavior (skill repo):** `contracts/command-router-contract.json` maps native slash commands to **`scripts/rfo_execute.py`**; `contracts/entrypoint-contract.json` documents **`canonical_operator_research_entrypoint`** vs queued-worker `required_entrypoint`; `contracts/supported-skill-actions-v1.json` — IDE/registry mirror; validators accept **`entrypoint-proof.json`** from either **`rfo_execute.py`** or historical **`run_research_factory.py`**; `tests/test_legacy_grave_markers.py`; SKILL/runtime-paths guest-preflight table expanded (forbidden env, secondary relay deprecated).

### 19.4.5 — 2026-05-13

- **Research plan on disk + early `run_dir`:** `research-plan-v1` contract, `RFO_RESEARCH_PLAN_MODE=off|llm_v1`, bridge allocates run directory before relay; adapter reuse via `RFO_PREALLOCATED_RUN_DIR`; `fanout_relay_search_from_queries`; plan validation in `validate_impl` when present; ADR-021; `jl()` ResourceWarning fix; `tests/test_research_plan_bridge.py`.
- **Operators:** `docs/operators/openclaw-gateway-rfo-notes.md` § B0 — Telegram/session JSON where `/research_factory_orchestrator` arrives as plain `type:text` (not native skill dispatch); transcript lint via `validate_rfo_command_did_not_spawn_plain_subagent.py`; cross-links in `SKILL.md` and `docs/runtime-paths.md`.

### 19.4.4 — 2026-05-10

- **Bridge / relay:** worker exit semantics hardened; `bridge.worker_poll` events appended to `latest_run/observability-events.jsonl`; non-zero exit when the inner worker fails after claim.
- **Canonical entrypoint:** `scripts/rfo_execute.py` as thin façade over `scripts/run_rfo_with_web_search.py` for native relay; `run_rfo_with_web_search.py` remains the bridge implementation; docs prefer the façade in new compose and operator notes.
- **Outbox:** `runtime/outbox_impl.py` — per-run coordination and `package_gate` semantics aligned with zip OUT-0005/OUT-0006 (E7).
- **Docs:** `docs/adr/ADR-020-vacuum-of-agency-degraded-modes.md`; `docs/operators/openclaw-gateway-rfo-notes.md`; runtime-paths, lease runbook, playbook, and search-primary profile notes updated.

### 19.4.3 — 2026-05-10 (internal plan **19.4.1.1** / accumulated fixes)

- **RAF / citation grounding:** `runtime/citation_grounding.py` — structural multiplier `min(1, support_count)` plus `inferred_assessment` weight **0.68** so relay/dossier rows with one grounded support can meet RAF ≥ 0.65 (previous `min(sc/2,1)*0.52` capped inferred claims below the threshold forever).
- **Sources schema:** `runtime/source_record_v19.py` — shared normalization for bridge + `run_rfo_full_research.py`; standalone driver emits **only** `schemas/core/sources.schema.json` fields (no `content` / legacy enums on disk).
- **Harness:** `scripts/run_core_validators.py` chain adds **`validate_citation_grounding`**; `validation-profiles/dossier.json` and **`search-primary.json`** list it. `validate_citation_grounding.py` — if the result file is missing and the profile does **not** require grounding, **pass** with warning (optional artifact).
- **Discovery frontmatter:** `validate_skill_discovery_frontmatter.py` accepts **19.4.x** (and keeps **19.3.x**).
- **Operator plan:** `docs/plans/PLAN-19.4.1.1-accumulated-fixes.md`; host embedding truncation prompt: `prompts/host-agent-embedding-truncate.md`.

- **`runtime_job_worker` packaging:** calls **`ensure_pkg_required_paths`** immediately before **`build_package`** so required ZIP paths exist per `contracts/package-required-artifacts.json`.
- **Run profiles:** `contracts/run-profiles.json` default **`dossier`**; contract keys are **`dossier`** and **`search-primary`**. `runtime.profiles.resolve` is fail-closed (unknown `RFO_RUN_PROFILE` / CLI `--profile` → `ValueError`).
- Relay bridge **multi-vector fanout** (`scripts/rfo_query_fanout.py`, `contracts/query-fanout-config.json`) with stats on `collection-result.json` (`relay_query_fanout`, `query_vectors`).
- Removed **empty-relay mvr scaffold** path and `RFO_ALLOW_MVR_EMPTY_RELAY` user surface; empty relay exits non-zero.
- Publish policy: **`block_user_publish_when_collection_seed_only`** wired through `decide_publish_allowed` / outbox.
- ADR: `docs/adr/ADR-019-single-dossier-funnel.md`.
- **Breaking (JSON consumers):** honesty harness JSON field `validator_id` is now **`verify_skill_run_claims`**. Canonical script: `scripts/verify_skill_run_claims.py` (removed `scripts/verify_openclaw_run.py`).
- Downstream agent index: `agent-handoff/bundle-manifest.json` under each run-dir
  (contract `rfo-agent-handoff-bundle-v1`) lists prompt role files and key artifact paths.
- **Roadmap (not shipped in this minor):** richer **LLM-orchestrated** wave planning / sub-query generation should reuse existing discipline prompts (`prompts/source-quality-worker-prompt.md`, `templates/evaluation-rubric.md`, `templates/archetypes/report-archetypes.json`) and write each LLM step to disk with schema validation; predecessor-era chat/HTML templates remain reference-only under `templates/` and `reports/`.
- Default bridge profile **`dossier`**; relay base URL required (no baked search host).
- Removed in-tree Telegram delivery (`providers/telegram/`, `tools/agent_telegram/`)
  and optional golden diff helper; docs/schemas label legacy `telegram_messages` field.
- Outbox: missing provider adapter is `failed` with `PROVIDER-DELIVERY-ADAPTER-MISSING`,
  not silent `sent`. Feature matrix uses `external_user_visible_delivery_via_skill`.

## 19.2.1 — 2026-05-07

- Honesty hardening: canonical skill-path + runs-root guardrails with explicit
  refusal stamps (`RFO-NON-CANONICAL-SKILL-PATH`, `RFO-RUNS-ROOT-FORBIDDEN`).
- Telegram routing hardening: `chat_id` resolution `request -> argv -> env(consent) -> fail`
  and explicit `delivery_not_proven` flow without silent `stub_only` fallback.
- Verifier hardening: added lie classes for wrong skill path, wrong runs root,
  delivery stub without consent, and narrative without evidence.
- Smoke/repro wrappers: added `_smoke_v19_2_1_honesty.py` and
  `_smoke_v19_2_1_repro_baseline.py` (legacy repro scripts retired in v19-only cleanup).

## 19.2.0 — 2026-05-02

- Runtime truth restoration: v19 artifact emission, collection/coverage decoupling,
  work-unit completion guards, integration smokes (`_smoke_v19_2_*`).
- Telegram: real `sendMessage` path + operator `tools/agent_telegram/` + mock API
  smoke (`_smoke_telegram_real_send`).
- Release: POSIX subprocess `killpg` hardening in `validate_release.py`,
  `failure-corpus/index-v19.json` meta registry bump, `verify_openclaw_run.py`.

## 19.1.0 — 2026-04 (backfill)

- Multi-agent advisory stack + deterministic replay smokes (ADR-012/013).
- Release zip triad + clean-install smoke + coverage meta gate.

## 1.0.0
- Initial release: `research-factory-orchestrator` with default `AUTO_COMPILE_AND_EXECUTE`, global/item FSM, internal compiler + executor protocols, templates, JSON schemas, playbooks, init/validate scripts, examples, and regression tests.
