# D7 — Core schema selection & v19 strict drafts

## Runtime artifact filenames (v19 core)

| Logical artifact | File (run dir) | v19 strict draft |
|------------------|----------------|------------------|
| Sources bundle | `sources.json` | `drafts/schemas/core/sources.schema.json` |
| Evidence cards | `evidence-cards.json` | `drafts/schemas/core/evidence-cards.schema.json` |
| Claims registry | `claims-registry.json` | `drafts/schemas/core/claims-registry.schema.json` |
| Contradictions lite | `contradictions-lite.json` (conditional) | `drafts/schemas/core/contradictions-lite.schema.json` |
| Final answer gate | `final-answer-gate.json` | `drafts/schemas/core/final-answer-gate.schema.json` |
| Delivery manifest | `delivery-manifest.json` | `drafts/schemas/core/delivery-manifest.schema.json` |
| Validation transcript | `validation-transcript.json` | `drafts/schemas/core/validation-transcript.schema.json` |

**Note:** `validation-transcript.json` is **core** — runner and truth-gate depend on it; omitting its schema was a design gap, now closed.

## Mapping from existing `schemas/*.schema.json` (113 → 7)

| v19 draft | Based on | Key deltas |
|-----------|----------|------------|
| `sources.schema.json` | `source.schema.json` | Top-level bundle `{ schema_version, sources[] }`; each source: dimensions + `canonical_origin_id`, `citation_eligible`; **`role_for_claim` removed** (lives on claim.support_set) |
| `evidence-cards.schema.json` | `evidence-card.schema.json` | Array wrapper; require `source_ids` minItems 1 OR single `source_id` (pick one in impl — draft uses `source_ids`); `extracted_fact` or `excerpt` required; `additionalProperties: false` |
| `claims-registry.schema.json` | `claims-registry.schema.json` | Replace loose `items: object` with strict claim object + `support_set` |
| `contradictions-lite.schema.json` | new | Compact L1 rows + scan header |
| `final-answer-gate.schema.json` | `final-answer-gate.schema.json` | Add `overconfidence_risk`, contradiction scan echo |
| `delivery-manifest.schema.json` | `delivery-manifest.schema.json` | Add split booleans; tighten `additionalProperties` |
| `validation-transcript.schema.json` | `validation-transcript.schema.json` | Validator results uniform shape |

## Full L2 matrix

Stub `schemas/contradiction-matrix.schema.json` (`entries: [{}]`) is replaced in implementation. Design reference: `drafts/schemas/heavy/contradiction-matrix.schema.json` (non-normative until adopted).

## Conventions (all v19 drafts)

- `$schema: https://json-schema.org/draft/2020-12/schema`
- Root `schema_version` enum `["v19.0"]` (bump in implementation when frozen)
- `additionalProperties: false` on extensible objects unless explicitly documented
