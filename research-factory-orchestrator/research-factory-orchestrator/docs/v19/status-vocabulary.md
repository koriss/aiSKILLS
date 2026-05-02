# D11 — Status vocabulary freeze (v19)

## Claim status enum (frozen)

| Status | Meaning |
|--------|---------|
| `confirmed_fact` | Mechanically supported; meets claim-type threshold |
| `verified_estimate` | Numeric / modeled estimate with stated uncertainty |
| `reported_claim` | Reported by sources, not independently verified |
| `inferred_assessment` | Inference from indicators; **cap** for intent-style claims |
| `forecast_scenario` | Forward-looking scenario; **never** `confirmed_fact` |
| `disputed` | Credible conflicting evidence |
| `insufficient_evidence` | Trace incomplete or sources too weak |
| `contradicted` | Strong refutation |
| `lead_only` | Investigative lead / not evidentiary |

## Hard transition rules

1. `forecast_scenario` **⇏** `confirmed_fact` (ever).
2. `inferred_assessment` **⇏** `confirmed_fact` for `geopolitical_intent_assessment` claim types.
3. `reported_claim` **⇏** `confirmed_fact` for `narrative_propaganda` unless profile defines a **rare** upgrade path with origin + amplification + independent corroboration (default: no upgrade).
4. `lead_only` **cannot** be sole backing for any final factual sentence mapped to `confirmed_fact`.
5. `atrocity_related` default band: `disputed` or `reported_claim`; upgrade to `confirmed_fact` only per D1 policy lists + mandatory caveats.

## Confidence enum (orthogonal to status)

`high` | `medium` | `low` | `unknown`

Rule (V5): `confirmed_fact` requires `confidence: high` unless explicit exception documented in profile (default: **no** exception).

## Evidence / source default bands

- Raw social / short-form video defaults to **`lead_only`** at claim level unless upgrade requirements satisfied (D6).
