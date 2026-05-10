# RFO v19 — documentation hub

This directory contains **v19 specifications** (validators, schemas, CI vs runtime boundaries, failure fixtures) **and** materials from the original **design program**. The repository root **`runtime/`**, **`scripts/`**, and **`contracts/`** are **live** — not a future implementation phase. Current release line: **`19.3.x`** (see [`runtime/version.json`](../../runtime/version.json), [`CHANGELOG.md`](../../CHANGELOG.md)).

## Where to look first (current line)

| Topic | Location |
|-------|-----------|
| Skill semver + `failure_corpus_index_version` | [`runtime/version.json`](../../runtime/version.json) |
| What shipped when | [`CHANGELOG.md`](../../CHANGELOG.md), [`release-notes/`](../release-notes/) |
| Profile defaults vs scripts | [`PROFILE_DEFAULTS.md`](../PROFILE_DEFAULTS.md), [`contracts/run-profiles.json`](../../contracts/run-profiles.json) |
| Portable paths / workspace | [`adr/ADR-RFO_PORTABLE.md`](../adr/ADR-RFO_PORTABLE.md) |
| Compute-only skill vs host delivery | [`adr/ADR-016-compute-vs-delivery-split.md`](../adr/ADR-016-compute-vs-delivery-split.md) |

## Deliverables catalog (design-era IDs)

The table below is the **original v19 deliverables map**. Files remain stable anchors; **implementation** lives in the repo (e.g. core validators under `validators/core/`, frozen JSON Schemas under `schemas/core/`, drafts under `drafts/` where noted).

| ID | Document | Purpose |
|----|----------|---------|
| D1 | [profiles.md](./profiles.md) | Named profiles, auto-escalation rules, draft JSON under `drafts/validation-profiles/` |
| D2 | [validators-core.md](./validators-core.md) | Six core validators (V1–V6), I/O contract |
| D3 | [claim-type-source-strength.md](./claim-type-source-strength.md) | Claim types, thresholds, `support_set` roles |
| D4 | [confidence-calibration.md](./confidence-calibration.md) | `overconfidence_risk`, blocking vs warning |
| D5 | [contradiction-matrix-levels.md](./contradiction-matrix-levels.md) | L0/L1/L2, neutral rubric, scan metadata |
| D6 | [delivery-truth-core.md](./delivery-truth-core.md) | V6 minimal invariants, stub vs external split |
| D7 | [schemas-core.md](./schemas-core.md) | Core schema selection + strict drafts |
| D8 | [migration-map.md](./migration-map.md) | pre-v19 -> v19 mapping (16 DAG + 34 registry) |
| D9 | [ci-vs-runtime.md](./ci-vs-runtime.md) | Boundary, no `jq` in runtime |
| D10 | [failure-fixtures.md](./failure-fixtures.md) | Bad/good fixture plan before validators |
| D11 | [status-vocabulary.md](./status-vocabulary.md) | Frozen enums and status caps |
| D12 | [ADR-001-pragmatic-rigor.md](./ADR-001-pragmatic-rigor.md) | Stub pointer to canonical ADR in `docs/adr/` |
| D13 | [sacred-path-contract.md](./sacred-path-contract.md) | Single Sacred Path chain + validator mapping (`role_for_claim` rules) |
| D14 | [corpus-crawlers-book-memory.md](./corpus-crawlers-book-memory.md) | Crawler politeness, corpus vs book/reference memory, retrieval policy |
| D15 | [production-hardening-phase1.md](./production-hardening-phase1.md) | Zip attestations, install smoke, coverage meta-gate, run-events, etc. |
| D16 | [propaganda-io-neutrality.md](./propaganda-io-neutrality.md) | Forbidden machine ids vs neutral pattern/topic fields |
| — | [run-core-validators-spec.md](./run-core-validators-spec.md) | Runner contract (`run_core_validators.py`) |
| — | [DESIGN-REVIEW.md](./DESIGN-REVIEW.md) | Design-phase verification checklist (historical) |
| — | [IMPLEMENTATION-PHASE-1-HANDOFF.md](./IMPLEMENTATION-PHASE-1-HANDOFF.md) | Handoff notes (may be superseded by ADRs + release notes) |

## Drafts

- `drafts/validation-profiles/*.json` — reference payloads; the harness loads live profiles from **`validation-profiles/`** at the repo root when present.
- `drafts/schemas/core/*.schema.json` — strict v19 JSON Schema drafts (`draft 2020-12`).
- `drafts/schemas/heavy/contradiction-matrix.schema.json` — L2 matrix (non-default path).

Runtime validation consumes **frozen** copies under **`schemas/core/`** where wired (see [schemas-core.md](./schemas-core.md)).

## Parallel tracks (historical)

- **Legacy hardening** and **v19 implementation** milestones are reflected in [`CHANGELOG.md`](../../CHANGELOG.md) and ADRs rather than this README alone.
