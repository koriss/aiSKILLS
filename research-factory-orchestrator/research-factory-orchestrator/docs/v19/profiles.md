# D1 — Profiles manifest (v19)

## Goals

- **MVR** (Minimal Viable Rigor) is the default for most tasks.
- **Full Rigor** is explicit or auto-escalated **with a recorded reason** (never keyword-only magic).
- **Specialized** profiles extend Full with optional heavy modules; they do not replace the six core validators.

## Named profiles (documentation)

| Profile | Doc intent | JSON draft |
|---------|------------|------------|
| quick-research | Alias / marketing name for default shallow web research | use `mvr` |
| deep-due-diligence | Full rigor + L2 contradiction where needed | use `full-rigor` |
| book-verification | Book pipeline; canonical protocol single source | `book-verification.json` |
| propaganda-io-analysis | Neutral pattern mapping; KB reference-only | `propaganda-io.json` |
| market-research | Industry data emphasis; numerical thresholds | extend `full-rigor` in implementation |

Human-readable expansions live under `profiles/` in **implementation** phase; this design phase only commits **draft JSON** under `drafts/validation-profiles/`.

## Core validators (all profiles)

Every profile lists the same six IDs (V1–V6); **options** and **thresholds** differ:

1. `validate_artifact_schema` (V1)
2. `validate_traceability` (V2)
3. `validate_source_quality` (V3)
4. `validate_claim_status` (V4)
5. `validate_final_answer` (V5)
6. `validate_delivery_truth` (V6)

## Contradiction level by profile

| Profile | `contradiction_level` | Notes |
|---------|----------------------|--------|
| mvr | L0 default; L1 if conflicts detected | L0 must include scan metadata (see D5) |
| full-rigor | L1 minimum; L2 for flagged tasks | Full matrix schema when L2 |
| propaganda-io | L1 minimum; L2 encouraged | Same six validators; heavy narrative modules optional |
| book-verification | L1 typical | Citation + excerpt gates stricter |

## Auto-escalation (design rules)

**Forbidden:** escalate only on keywords (`propaganda`, `narrative`, `IO`) without structured signals.

**Required:** any auto-escalation writes:

- `auto_escalation_reason` (string, human-readable)
- `auto_escalation_signals` (array of enum hits, e.g. `high_source_conflict`, `sensitive_claim_type_mix`, `legal_high_stakes`)
- `user_override_allowed`: always `true` at framing time

Signals should come from **artifact state** (contradiction scan, claim types present, user-declared stakes), not substring matching on free text alone.

## Heavy modules (optional, not in MVR default path)

- Full contradiction matrix (L2)
- Laundering graph
- Timeline integrity deep check
- Narrative sponsorship graph

These are **profile-gated** and may ship under `heavy/` in implementation; they are not part of the portable six-validator core.

## Registry note

`contracts/validator-registry.json` (v18.5.1) contains **34** curated validators for CI / selective DAG — all receive a v19 destination in [migration-map.md](./migration-map.md).

## Draft files

See:

- `drafts/validation-profiles/mvr.json`
- `drafts/validation-profiles/full-rigor.json`
- `drafts/validation-profiles/propaganda-io.json`
- `drafts/validation-profiles/book-verification.json`
