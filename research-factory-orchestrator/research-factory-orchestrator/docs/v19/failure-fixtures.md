# D10 — Failure fixtures plan (v19)

## Principle

Schemas without **paired bad fixtures** regress into ceremony. Implementation phase **must** land fixtures **before** merging validator logic that depends on them.

## Directory layout (implementation)

```
tests/fixtures/v19/
  good/
    mvr_minimal_valid/
  bad/
    claim_without_evidence/
    evidence_without_source/
    evidence_source_id_unknown/
    confirmed_from_social_only/
    forecast_as_confirmed_fact/
    geopolitical_intent_as_confirmed_fact/
    raw_visual_without_context_confirmed/
    kb_match_used_as_evidence/
    duplicate_sources_counted_as_independent/
    final_answer_new_fact/
    local_path_in_user_message/
    cli_claimed_external_delivery/
    contradiction_required_but_missing/
    l0_scan_unknown_under_full_profile/
    release_pass_without_transcript/
```

## Fixture → expected failure class (logical)

| Fixture | Primary validator | Expected |
|---------|-------------------|----------|
| `claim_without_evidence` | V2 | blocking |
| `evidence_without_source` | V2 | blocking |
| `evidence_source_id_unknown` | V2 | blocking |
| `confirmed_from_social_only` | V3 / V4 | blocking (profile-sensitive) |
| `forecast_as_confirmed_fact` | V4 | blocking (status cap) |
| `geopolitical_intent_as_confirmed_fact` | V4 | blocking |
| `raw_visual_without_context_confirmed` | V3 / V4 | blocking |
| `kb_match_used_as_evidence` | V2 / V4 | blocking |
| `duplicate_sources_counted_as_independent` | V3 | blocking or warning |
| `final_answer_new_fact` | V5 | blocking |
| `local_path_in_user_message` | V6 | blocking |
| `cli_claimed_external_delivery` | V6 | blocking |
| `contradiction_required_but_missing` | V4 | blocking |
| `l0_scan_unknown_under_full_profile` | V4 / V5 | blocking |
| `release_pass_without_transcript` | CI release validator | blocking (dev contour) |

## Good fixture

`good/mvr_minimal_valid/` — smallest consistent run-dir passing **MVR** under all six validators.

## Failure corpus registration

Mapping these to `F2xx` classes and `failure-corpus/index.json` updates is **implementation phase** (explicitly out of design scope).
