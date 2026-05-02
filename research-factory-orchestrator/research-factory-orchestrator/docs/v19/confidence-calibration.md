# D4 — Confidence calibration (V5)

## `overconfidence_risk` object (in `final-answer-gate.json` or sidecar per D7)

```json
{
  "overconfidence_risk": {
    "blocking": [],
    "warnings": [],
    "signals": {
      "absolute_statements_in_text": [],
      "single_source_strong_claim": [],
      "effective_independent_support_lt_required": [],
      "origin_count_eq_1_with_amplification": [],
      "recent_event_with_old_sources": false,
      "weak_source_supporting_strong_claim": [],
      "causal_language_without_causal_evidence": [],
      "confirmed_with_non_high_confidence": [],
      "new_fact_sentences_without_claim_id": []
    }
  }
}
```

## Severity policy

**Rule:** V5 fails (`passed=false`, `blocking=true`) iff **`blocking[]` non-empty** OR structural gate failures (e.g. new facts). Non-empty `warnings[]` alone does **not** fail MVR unless profile elevates specific warnings.

### Suggested default blocking codes

| Code | Condition |
|------|-----------|
| `NEW_FACT_WITHOUT_CLAIM_ID` | Parsed final sentences introduce factual content not mapped to `claim_id` |
| `ABSOLUTE_WITHOUT_HIGH_CONFIDENCE` | Absolutist markers in final text without backing claims all `high` confidence |
| `CAUSAL_LANGUAGE_WITHOUT_CAUSAL_EVIDENCE` | Causal verbs tied to claims lacking causal evidence type |
| `CONFIRMED_WITH_NON_HIGH_CONFIDENCE` | Claim status `confirmed_fact` while claim.confidence ≠ `high` |
| `STATUS_CAP_VIOLATION` | May also be caught in V4 — duplicate in V5 optional |

### Suggested default warnings

| Code | Condition |
|------|-----------|
| `RECENT_EVENT_OLD_SOURCES` | Event recency vs source publication dates mismatch |
| `SINGLE_SOURCE_STRONG_PRIMARY` | Only one origin but source is court/primary — review, not auto-fail |
| `WEAK_SOURCE_MEDIUM_CLAIM` | Borderline quality |

## Detection helpers

### Absolutist markers (configurable list)

English / Russian examples (non-exhaustive): `always`, `never`, `all`, `none`, `proves`, `definitely`, `безусловно`, `однозначно`, `доказано`, `все знают`, …

Matcher must be **conservative** (avoid natural language false positives); tie-break goes to human review flag.

### `effective_independent_support_count`

Count **distinct** `canonical_origin_id` among `support_set` where role ∈ {`primary_support`, `corroboration`}.

### `origin_count_eq_1_with_amplification`

True if graph / ledger shows multi-hop amplification from single origin cluster (implementation detail in heavy module; V5 consumes summary flags).

## Profile interaction

- **MVR:** warnings preferred for borderline absolutist language if claims are high-confidence and well-cited.
- **Full / propaganda-io:** stricter promotion of warnings to blocking when stakes flags set.
