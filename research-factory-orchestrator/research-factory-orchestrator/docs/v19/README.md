# RFO v19 — Pragmatic Rigor (design phase)

This directory contains **design-only** artifacts for v19. No changes to active `runtime/`, `scripts/`, or `contracts/` until implementation phase.

## Deliverables

| ID | Document | Purpose |
|----|----------|---------|
| D1 | [profiles.md](./profiles.md) | Named profiles, auto-escalation rules, draft JSON under `drafts/validation-profiles/` |
| D2 | [validators-core.md](./validators-core.md) | Six core validators (V1–V6), I/O contract |
| D3 | [claim-type-source-strength.md](./claim-type-source-strength.md) | Claim types, thresholds, `support_set` roles |
| D4 | [confidence-calibration.md](./confidence-calibration.md) | `overconfidence_risk`, blocking vs warning |
| D5 | [contradiction-matrix-levels.md](./contradiction-matrix-levels.md) | L0/L1/L2, neutral rubric, scan metadata |
| D6 | [delivery-truth-core.md](./delivery-truth-core.md) | V6 minimal invariants, stub vs external split |
| D7 | [schemas-core.md](./schemas-core.md) | Core schema selection + link to strict drafts |
| D8 | [migration-map.md](./migration-map.md) | v18 → v19 mapping (16 DAG + 34 registry) |
| D9 | [ci-vs-runtime.md](./ci-vs-runtime.md) | Boundary, no `jq` in runtime |
| D10 | [failure-fixtures.md](./failure-fixtures.md) | Bad/good fixture plan before validators |
| D11 | [status-vocabulary.md](./status-vocabulary.md) | Frozen enums and status caps |
| D12 | [ADR-001-pragmatic-rigor.md](./ADR-001-pragmatic-rigor.md) | Stub pointer to canonical ADR in `docs/adr/` |
| D13 | [sacred-path-contract.md](./sacred-path-contract.md) | Single Sacred Path chain + validator mapping (`role_for_claim` rules) |
| D14 | [corpus-crawlers-book-memory.md](./corpus-crawlers-book-memory.md) | Crawler politeness, corpus vs book/reference memory, retrieval policy |
| D15 | [production-hardening-phase1.md](./production-hardening-phase1.md) | Zip attestations, install smoke, coverage meta-gate, run-events, etc. |
| D16 | [propaganda-io-neutrality.md](./propaganda-io-neutrality.md) | Forbidden machine ids vs neutral pattern/topic fields |
| — | [run-core-validators-spec.md](./run-core-validators-spec.md) | Runner contract (`run_core_validators.py`) |
| — | [DESIGN-REVIEW.md](./DESIGN-REVIEW.md) | Design-phase verification checklist |
| — | [IMPLEMENTATION-PHASE-1-HANDOFF.md](./IMPLEMENTATION-PHASE-1-HANDOFF.md) | Next implementation scope |

## Drafts (not wired into repo root until implementation)

- `drafts/validation-profiles/*.json` — profile payloads
- `drafts/schemas/core/*.schema.json` — strict v19 core JSON Schemas (draft 2020-12)
- `drafts/schemas/heavy/contradiction-matrix.schema.json` — L2 matrix (non-default path)

## Parallel tracks

- **v18.7**: production-mode + logical consistency validator (separate plan).
- **v19 implementation**: starts after design sign-off.
