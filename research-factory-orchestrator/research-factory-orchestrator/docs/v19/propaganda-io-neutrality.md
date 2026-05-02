# Propaganda-IO — neutrality contract for machine fields (v19)

`propaganda-io` is **pattern mapping and traceability**, not a verdict engine “who is right”. Human analysts may write interpretive prose in narrative notes; **system enums, pattern ids, JSON keys must stay neutral.**

## Forbidden in machine-visible identifiers

Do **not** use these (non-exhaustive) in automated pattern ids, system enums, or schema-required strings:

- Moral/partisan roles: `aggressor`, `victim`, `terrorist`, `martyr`, `just_side`, `*_wins`
- Loaded verdict motifs: `atrocity_denial`, `genocide_denial`, `traitor`, `fake_news` as classifier labels
- Victim/perpetrator framing as **taxonomy keys** (fine in human text, not as machine id)

This aligns with [contradiction-matrix-levels](./contradiction-matrix-levels.md): interpretive language belongs in human-authored notes after an explicit reasoning chain, not baked into L2 rubric enums.

## Claim topics vs narrative patterns

- **Claim topics** (`claim_topics_*` in profile JSON): *descriptive routing* — which claim-type/status-cap bundle applies (e.g. harm attribution, intent assessment). Wording must be factual-domain, not moral verdict.

- **Narrative patterns** (`narrative_patterns_*`): *structural* descriptors of communication mechanics (compression, amplification, omission, reframing). They must cite **source spans + explanation + alternative hypothesis** per profile rules ([draft `propaganda-io.json`](./drafts/validation-profiles/propaganda-io.json)).

## KB

KB matches are **reference-only**: never `kb_*` ids as factual `source_id`; never raises claim status ([profiles](./profiles.md)).

## Review

Editors run [DESIGN-REVIEW](./DESIGN-REVIEW.md) neutrality checklist before freezing profile JSON.
