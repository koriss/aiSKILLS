# Research Factory Orchestrator — v19 core operator sheet

**Version:** `19.3`  
**ADR:** `docs/adr/ADR-001-v19-pragmatic-rigor.md`  
**Runtime truth:** `docs/adr/ADR-015-runtime-truth-restoration.md`

## Role

OpenClaw skill for research orchestration with artifact-first compute, profile-driven validation, and delivery truth gating.

## Eight-phase pipeline

1. Intake
2. Context
3. Acquisition
4. Synthesis
5. Contradiction scan
6. Final answer gate
7. Validation
8. Delivery

## Sacred path

Every factual claim must trace through claim -> evidence -> source with explicit ids.

## V1–V6

- V1 `validate_artifact_schema`: artifacts parse and satisfy v19 schema.
- V2 `validate_traceability`: sacred path consistency.
- V3 `validate_source_quality`: source role and independence constraints.
- V4 `validate_claim_status`: claim status, caps, contradiction guards.
- V5 `validate_final_answer`: risk blocks and final gate semantics.
- V6 `validate_delivery_truth`: artifact/delivery consistency and no fake delivery.

## Profiles

- `mvr`
- `full-rigor`
- `propaganda-io`
- `book-verification`

Run:

`python -S scripts/run_core_validators.py --run-dir <run_dir> --profile mvr`

## Logical consistency (LC01–LC16)

`scripts/validate_logical_consistency.py` remains an explicit parallel gate for release/failure-corpus workflows.
