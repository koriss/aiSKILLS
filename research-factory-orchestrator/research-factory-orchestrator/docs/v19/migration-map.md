# D8 — Migration map (v18.5.1 → v19)

## Scope policy (design phase)

| Bucket | Design obligation |
|--------|-------------------|
| 17 `run_dir_first` DAG validators (`runtime/validate_impl.py`) | **Full** mapping → V1–V6 |
| 35 `validator-registry.json` entries (v19.0.1) | **Full** destination tag per id |
| ~150 orphan `scripts/validate_*.py` | **Inventory summary + policy only** (no per-file decision) |
| 132 references / 4 failure-corpus overlays | **Bucket-level** policy (core / heavy / legacy) |

## Six core validators — absorption map (17 DAG)

| v18.5.1 DAG validator | v19 core | Rationale |
|----------------------|----------|-----------|
| `validate_schema_field_coverage` | **V1** | Schema / field coverage gate |
| `validate_skill_markdown_injection` | **V1** | Structural / injection safety |
| `validate_skill` (always-run) | **V1** | Package integrity prerequisite |
| `validate_handoff_envelope` | **V2** | Cross-artifact linkage / trace envelope |
| `validate_citation_grounding` | **V2** (+ **V3**) | Citations ↔ evidence ↔ sources |
| `validate_quote_supports_claim` | **V2** | Quote-evidence-claim alignment |
| `validate_semantic_intent_alignment` | **V4** | Claim / intent consistency |
| `validate_capability_scope` | **V4** | Scope vs evidence strength |
| `validate_state_transitions` | **V4** | Lifecycle / status machine |
| `validate_snapshot_immutability` | **heavy** | Integrity / replay — not sacred-path core |
| `validate_cross_model_judge` | **heavy** | Optional adversarial depth |
| `validate_trace_hash_chain` | **heavy** | Provenance chain beyond MVR |
| `validate_replay_determinism` | **heavy** | Determinism / CI depth |
| `validate_outgoing_message_claims` | **V5** + **V6** | User-visible text vs manifests |
| `validate_idempotent_outbox` | **V6** | Delivery / outbox truth |
| `validate_no_delivery_after_validation_fail` | **V6** | Fail-closed rollback companion |
| `validate_no_local_paths_in_chat` | **V6** | Path leak (extend to all user-visible artifacts in v19) |

## Registry (35) — destination tags

| Destination | Meaning |
|-------------|---------|
| `core` | Implemented inside or invoked by V1–V6 in v19 |
| `heavy` | Profile-gated optional validators |
| `legacy` | Archived scripts; not in default DAG |
| `ci-only` | Repository QA, not OpenClaw runtime |

All registry ids from `contracts/validator-registry.json` v19.0.1:

| id | destination |
|----|---------------|
| `validate_skill` | core (V1) |
| `validate_delivery_manifest` | core (V6) |
| `validate_schema_field_coverage` | core (V1) |
| `validate_handoff_envelope` | core (V2) |
| `validate_semantic_intent_alignment` | core (V4) |
| `validate_smoke_run_not_presented_as_research` | ci-only |
| `validate_snapshot_immutability` | heavy |
| `validate_outgoing_message_claims` | core (V5/V6) |
| `validate_citation_grounding` | core (V2/V3) |
| `validate_idempotent_outbox` | core (V6) |
| `validate_user_visible_delivery_ack` | core (V6) |
| `validate_status_claim_consistency` | core (V4) |
| `validate_self_claim_not_external_confirmation` | core (V6) |
| `validate_summary_no_new_facts` | core (V5) |
| `validate_summary_no_new_claims` | core (V5) |
| `validate_telegram_no_tables_strict` | heavy |
| `validate_telegram_plain_text` | heavy |
| `validate_telegram_message_lengths` | heavy |
| `validate_stub_delivery_not_external` | core (V6) |
| `validate_seed_claims_not_presented_as_domain_analysis` | core (V4) |
| `validate_snippet_only_not_confirmed` | core (V4) |
| `validate_snippet_only_not_full_report` | heavy |
| `validate_source_gap_reflected_in_final_verdict` | core (V5) |
| `validate_timeout_reflected_in_claim_caps` | core (V4) |
| `validate_tool_call_claims` | heavy |
| `validate_cross_model_judge` | heavy |
| `validate_trace_hash_chain` | heavy |
| `validate_capability_scope` | core (V4) |
| `validate_replay_determinism` | heavy |
| `validate_state_transitions` | core (V4) |
| `validate_skill_markdown_injection` | core (V1) |
| `validate_quote_supports_claim` | core (V2) |
| `validate_no_delivery_after_validation_fail` | core (V6) |
| `validate_no_local_paths_in_chat` | core (V6) |
| `validate_logical_consistency` | **post_validation** (v18.7 LC01–LC16; not part of V1–V6 core chain) |

> Note: registry version `19.0.1` lists **35** validators (includes `validate_logical_consistency`).

## Failure corpus overlays

Collapse 4 overlay indexes → `failure-corpus/index-v19.json` + move overlays to `legacy/failure-corpus/` (implementation).

## SKILL.md

2255-line SKILL → `SKILL-core.md` (≤300 lines). Duplicate `legacy/SKILL-overlays/SKILL.md` removed in v19.0.1 (single `SKILL.md` source).

## Package diet (pointer)

Active runtime allowlist, KB relocation, single runner — see `ADR-001-pragmatic-rigor.md` §Package diet.
