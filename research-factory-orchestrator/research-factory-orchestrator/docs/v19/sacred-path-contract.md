# Sacred Path — machine contract (v19)

Single source of truth for the **bottom-up** research chain. Anything that reaches the user as asserted fact must traverse this path; no parallel “top-down” fact assembly.

## Chain (obligatory order)

1. **Source** — canonical record in `sources` (see [schemas-core](./schemas-core.md)); stable properties only. No `role_for_claim` on the source row.
2. **Evidence card** — minimum proof unit pointing at ≥1 existing `source_id`, with excerpt or structured extract **and** a resolvable locator/selector where the profile demands it ([validators-core](./validators-core.md) V2).
3. **Claim** — normalized thesis with `support_set[]` carrying `{ source_id, evidence_card_id, role_for_claim }`. Only `primary_support` and `corroboration` count toward independence / thresholds unless profile says otherwise.
4. **Final sentence** — user-visible factual wording compiled **only** from claims via an explicit mapping (`claim_ids`); no orphan sentences.

Formal analogues: separation of derivation layers aligns with provenance vocabularies (e.g. W3C PROV) and addressable excerpts (e.g. Web Annotation selectors). Implementation may use bundled JSON artifacts under the run layout agreed in D7; this document binds **logical** dependencies, not on-disk paths.

## Hard rules (fail-closed)

| Rule | Enforcement |
|------|--------------|
| Claim with zero evidence cards | **Block** (V2). |
| Evidence card referencing missing / non-resolvable source | **Block** (V2). |
| `role_for_claim` only in `claims` / `support_set`, never as sole attribution on `source` | V2 + schema `additionalProperties` where frozen. |
| Final factual content without `claim_id` trace | **Block** (V5). |
| KB / internal memory row used as factual `source_id` in trace | **Block** ([profiles](./profiles.md), V3/V4). |
| `confirmed_fact` (or capped equivalent) without claim-type threshold on support-set | **Block** (V4). |

## Effective independence

Independent support counts use **`canonical_origin_id`** (or successor field in bundle schema), never raw URL count alone. Laundry / syndication duplicates must collapse before threshold checks (V3).

## Relation to validators

| Validator | Sacred Path slice |
|-----------|-------------------|
| V1 | Artifacts parse + `schema_version` / required keys. |
| V2 | Full chain integrity + support roles. |
| V3 | Source dimensions + citation eligibility + origin dedup. |
| V4 | Status caps, contradiction-lite obligations, social/visual caps. |
| V5 | Final text ↔ claims; overconfidence; **no embedded instruction-following from crawled blobs** ([production-hardening-phase1](./production-hardening-phase1.md)). |
| V6 | Delivery truth vs validation outcome. |

## Out of scope here

Operational crawling, WARC stores, vector indexes — see [corpus-crawlers-book-memory](./corpus-crawlers-book-memory.md). They feed **upstream** production of sources/evidence; they do not shorten or bypass this contract.
