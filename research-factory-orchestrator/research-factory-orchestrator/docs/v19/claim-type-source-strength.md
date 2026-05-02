# D3 — Claim type → source strength matrix (v19)

## Principle

Thresholds apply to **`support_set` roles `primary_support` and `corroboration` only** (see D2). Other roles provide context but **must not** satisfy confirmation requirements.

## Multidimensional source model (no numeric trust score)

Each `source` record (in `sources.json`) carries categorical dimensions, for example:

| Dimension | Example enum values |
|-----------|---------------------|
| `source_role` | `official`, `court`, `registry`, `dataset_publisher`, `peer_reviewed`, `journalist`, `ngo`, `activist`, `corporate`, `osint`, `witness`, `anonymous`, `unknown` |
| `access_level` | `primary_access`, `secondary`, `derivative`, `unknown` |
| `interest_alignment` | `direct`, `indirect`, `none`, `unknown` |
| `verification_mode` | `raw_document`, `dataset`, `visual`, `testimony`, `aggregation`, `opinion` |
| `independence` | `high`, `medium`, `low`, `unknown` |
| `authority_scope` | array of scoped tags, e.g. `military`, `legal`, `medical`, `economic`, `technical` |
| `corroboration_type` | `independent`, `circular`, `unknown` |

**`canonical_origin_id`:** stable dedup key for independence counting (see V3). Duplicate URLs / syndicated copies must collapse.

## Claim types (minimum set)

| Claim type | Meaning | Min support for “strong” status (see D11 for exact status names) | Notes |
|------------|---------|-------------------------------------|-------|
| `factual_event` | Discrete occurrence | Primary document **or** multiple independent strong | Social-only blocked for confirmed |
| `numerical_statistical` | Quantities, rates | Official statistics / recognized dataset / UN-WHO-IMF-SIPRI class | Ranges mandatory for estimates |
| `legal` | Norms, rulings | Primary legal instrument or court record | |
| `scientific_empirical` | Empirical science | Peer-reviewed, preregistered study, or authoritative dataset | |
| `causal` | Causal mechanism | RCT, strong natural experiment, or validated causal model | Correlation from media ≠ causal |
| `geopolitical_factual_event` | Geo-political fact claims | Official doc **or** multiple independent | |
| `geopolitical_capability_estimate` | Hardware/ORBAT/etc. | Primary + industry / satellite / gov where applicable | Must be `verified_estimate` band, not bare `confirmed_fact` unless policy allows |
| `geopolitical_intent_assessment` | Intent / goals | **Status cap:** `inferred_assessment` max | Never `confirmed_fact` |
| `geopolitical_forecast` | Forward scenario | **Status cap:** `forecast_scenario` max | Never `confirmed_fact` |
| `narrative_propaganda` | Narrative / framing | **Status cap:** `reported_claim` max unless rare upgrade path in profile | Requires origin + amplification map in propaganda-io |
| `atrocity_related` | Mass harm, war crimes allegations | Default cap `disputed_or_reported`; upgrade only with D1 policy lists | Caveats mandatory |

## `role_for_claim` (claim-scoped, **not** on `Source`)

Per claim, `support_set[]` entries:

```json
{
  "source_id": "S-12",
  "evidence_card_id": "E-44",
  "role_for_claim": "primary_support"
}
```

Allowed roles: `primary_support`, `corroboration`, `context`, `lead`, `opposition`.

## Weak-source rules

- Anonymous / unauthenticated social **cannot** be sole `primary_support` for `confirmed_fact` on sensitive types.
- Raw visual without geolocation/timestamp/manipulation posture stays **`lead_only`** at evidence level (see propaganda-io profile).
