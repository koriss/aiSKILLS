# Phase 3 schema dedup

- Decision: keep both files, but mirror `schemas/final-answer-gate.schema.json` to `schemas/core/final-answer-gate.schema.json` content.
- Rationale: no direct runtime readers of the legacy path were found; contract lists only schema basename, so mirroring avoids accidental divergence while preserving backward compatibility.

## Reader scan

- `validators/core/validate_artifact_schema.py` uses `SCHEMA_DIR = schemas/core` and reads `final-answer-gate.schema.json` from there.
- `contracts/schema-strictness-contract.json` only references filename `final-answer-gate.schema.json`.

## Applied fix

- Replaced legacy `schemas/final-answer-gate.schema.json` with exact copy of `schemas/core/final-answer-gate.schema.json`.
