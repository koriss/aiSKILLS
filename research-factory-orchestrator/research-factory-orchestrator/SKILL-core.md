# Research Factory Orchestrator — v19 core operator sheet

**Version:** `19.0.2` · **ADR:** `docs/adr/ADR-001-v19-pragmatic-rigor.md` · **Handoff:** `docs/v19/IMPLEMENTATION-PHASE-1-HANDOFF.md` · **Patch notes:** `docs/release-notes/v19.0.2.md` · **Legacy full overlay:** `SKILL.md` (v18.x retained)

**Deprecation:** subagent / durable work-unit / shard-ledger flows remain **legacy-only** (see `SKILL.md`, `references/work-unit-contract.md`). The v19 **core path** is profiles + V1–V6 + `run_core_validators.py`; do not mix undocumented subagent overrides with `RFO_V19_PROFILE` runs.

## Role

OpenClaw skill: orchestrate research runs, gate delivery truth, and emit audit-ready artifacts. v19 adds **six core validators** (V1–V6) behind `scripts/run_core_validators.py` and frozen schemas under `schemas/core/`.

## Eight-phase pipeline (conceptual)

1. **Intake** — task envelope, mode (`research` / `production` / `smoke`), provider caps.  
2. **Context** — bounded context packets; no ambient override of SKILL/runtime contracts.  
3. **Acquisition** — sources brokered per policy; KB usage explicit per profile.  
4. **Synthesis** — claims registry + evidence cards; sacred path **claim → evidence → source**.  
5. **Contradiction / scan** — L0–L2 per profile; `unknown` under **full-rigor** blocks pass.  
6. **Final answer** — `final-answer-gate.json` with `overconfidence_risk` blocking codes (see D4).  
7. **Validation** — legacy DAG **or** v19 core: set `RFO_V19_PROFILE` to `mvr` | `full-rigor` | `propaganda-io` | `book-verification` to run V1→V6 instead of the v18 DAG.  
8. **Delivery** — delivery-manifest truth split: artifact-ready vs external delivery; fail-closed rollback on validation fail (v18.5.1 preserved).

## Sacred path

Every factual claim must trace through **primary_support** / **corroboration** roles in `claims-registry.support_set` to an evidence card with **non-empty `source_ids`** resolving to `sources.json`. Snippet/lead roles cannot justify `confirmed_fact`.

## Status vocabulary (caps)

`forecast` → max `forecast_scenario`; `geopolitical_intent_assessment` → max `inferred_assessment`; social-only or raw visual cannot back `confirmed_fact`. Profiles tighten **blocking_rules** and **claim_type_policies** (see `validation-profiles/*.json`).

## V1–V6 (one line each)

| Id | Role |
|----|------|
| V1 `validate_artifact_schema` | Core JSON artifacts present, parseable, `schema_version` **v19.0**. |
| V2 `validate_traceability` | Sacred path; evidence must list sources; graph consistent. |
| V3 `validate_source_quality` | Independence via `canonical_origin_id`; KB ids not counted as factual evidence. |
| V4 `validate_claim_status` | Status caps + lite contradictions when required + L0 unknown under full profile. |
| V5 `validate_final_answer` | `overconfidence_risk.blocking` / `warnings` / `signals` from final gate. |
| V6 `validate_delivery_truth` | Manifest vs hashes; CLI ⇒ no real external delivery; path-leak checks. |

## Profile pick

- **`mvr`** — default minimal rigor, fast gate.  
- **`full-rigor`** — stricter contradiction + L0 unknown blocks.  
- **`propaganda-io`** — IO laundering checks; `kb_match_is_evidence: false` enforced in profile JSON.  
- **`book-verification`** — book-grade corroboration thresholds.

Run: `python -S scripts/run_core_validators.py --run-dir <run_dir> --profile mvr`. CI pass check: `python -S scripts/check_validation_pass.py --run-dir <run_dir>`.

## v18.7 logical consistency (parallel)

`scripts/validate_logical_consistency.py` remains in **release** and **failure corpus** paths (LC01–LC16). Not replaced by V1–V6.

## Migration

`python -S scripts/migrate_validator_invocation.py` prints (or `-o file`) legacy registry id → v19 runner mapping. **`failure-corpus/index-v19.json`** lists overlays + v19 fixture roots.

## Compatibility

Full historical SKILL text lives in **`SKILL.md`** only (overlay duplicate removed in v19.0.2). Runtime version: `runtime/version.json`.
