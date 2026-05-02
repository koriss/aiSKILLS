# ADR-001 — RFO v19 Pragmatic Rigor

## Status

Accepted (design phase) — 2026-05-02

## Context

- v18.5.1 fixed critical delivery/validation truth gaps but the skill remains **ceremony-heavy** (2255-line SKILL, 189 validators, 16 active in DAG, ~150 orphan).
- Sacred Path (Source → Evidence → Claim) is declared but not uniformly fail-closed.
- `propaganda-io` KB is large (~18MB) and risks being mistaken for **evidence** rather than **reference**.
- Contradiction matrix documentation/schema is largely a stub.
- Runtime vs CI tooling boundaries blurred in places (e.g. `jq` assumptions).

## Decision

1. Introduce **MVR** default + **Full Rigor** + **specialized profiles** (`propaganda-io`, `book-verification`, …).
2. Freeze **six core validators** (V1–V6) as the only portable runtime validation chain.
3. Sacred Path extended to final user text: **Source → Evidence Card → Claim → Final Sentence** (claim_id mapping).
4. **Status vocabulary** frozen (D11); **status caps** enforced mechanically for sensitive claim types.
5. **Multidimensional** source assessment — **no** single numeric trust score as gate.
6. **propaganda-io** remains neutral rubric + pattern mapping; KB match is **never** evidence.
7. **Delivery truth** stays core operational safety but minimal: split `artifact_ready` vs `external_delivery` (D6).
8. **Schemas + bad fixtures precede validator code** in implementation sequencing.

## Core invariants (machine-checkable)

- Claim without ≥1 evidence card → **block**
- Evidence card without resolvable source id → **block**
- `confirmed_fact` without meeting claim-type threshold on support-set → **block**
- Final text factual content without `claim_id` mapping → **block**
- External delivery claim without real proof or explicit stub disclosure → **block**
- CLI/local provider ⇒ `real_external_delivery=false` always
- No absolute local paths in user-visible artifacts
- KB ids must not appear as factual `source_id` in trace chain
- L0 contradiction: `high_severity_detected: unknown` **blocks** Full / propaganda profiles

## Package diet (active surface)

- Maintain **allowlist** for runtime-relevant paths in OpenClaw install.
- Move long-form docs, legacy overlays, deep KB to **`legacy/`** or **`references/`** not loaded by default MVR.
- One **`SKILL-core.md`** (≤300 lines) + archived overlays.
- One **`run_core_validators.py`** runner.

## Runtime vs dev boundary

See [D9 ci-vs-runtime](../v19/ci-vs-runtime.md).

## Non-goals (v19 design)

- No new proliferation of validators in core (>6).
- No political verdict enums in system schema.
- No default Full Rigor.
- No CI-only tools required inside OpenClaw runtime.
- No Markdown-as-source-of-truth for release claims without machine-readable sidecar (follow-up ADR).

## Consequences

- Large migration / collapse of SKILL + validator DAG in implementation phase.
- v18.7 logical-consistency track remains independent hotfix until merged.

## References

- `docs/v19/README.md`
- Draft schemas: `docs/v19/drafts/schemas/core/`
- Draft profiles: `docs/v19/drafts/validation-profiles/`

### Supplementary design (post–design-phase synthesis)

Canonical machine contract for derivation order: [`docs/v19/sacred-path-contract.md`](../v19/sacred-path-contract.md).

Crawler/corpus/book memory boundaries (design-only stack guidance): [`docs/v19/corpus-crawlers-book-memory.md`](../v19/corpus-crawlers-book-memory.md).

`propaganda-io` machine-field neutrality rules: [`docs/v19/propaganda-io-neutrality.md`](../v19/propaganda-io-neutrality.md).

Release/install/coverage recommendations around phase 1: [`docs/v19/production-hardening-phase1.md`](../v19/production-hardening-phase1.md).
