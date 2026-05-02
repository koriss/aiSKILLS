# D5 — Contradiction matrix levels (L0 / L1 / L2)

## Neutral rubric (L1/L2 entries)

Each contradiction record MUST include rubric facets — **no** pre-baked political verdict fields:

```json
{
  "source_role": "conflict_party | official | ngo | academic | journalist | osint | witness | unknown",
  "interest_alignment": "direct | indirect | none | unknown",
  "access_level": "primary_access | secondary | derivative | unknown",
  "verification_mode": "raw_data | visual | document | testimony | aggregation | opinion",
  "independence": "high | medium | low | unknown",
  "corroboration": "independent | circular | unknown"
}
```

**Forbidden in schema / enums:** `*_wins`, `aggressor`, `victim`, `terrorist`, `atrocity_denial`, `human_shield_inversion` as *system* labels. Interpretive language belongs only in **human-authored** `resolution.notes` after explicit reasoning chain.

## Levels

### L0 — Lite default

**When:** quick-research / MVR baseline.

**Artifacts:** may omit full matrix file **only** if scan metadata proves low conflict environment.

**Required fields (final-answer-gate or contradictions-lite header):**

```json
{
  "contradiction_level": 0,
  "contradiction_scan_performed": true,
  "scan_scope": "sources_and_claims_lite",
  "high_severity_detected": false
}
```

If scan not performed:

```json
{
  "contradiction_level": 0,
  "contradiction_scan_performed": false,
  "high_severity_detected": "unknown"
}
```

**Rule:** For **Full** / **propaganda-io** / high-stakes, `unknown` **must not** pass (blocking).

### L1 — Compact table

**When:** adversarial topics, numerical mismatch >10%, timeline inconsistency, propaganda profile default.

**Artifact:** `contradictions-lite.json` (see draft schema) with compact rows:

`claim_id`, `conflict_type`, `source_a`, `source_b`, `severity`, `resolution_status`, `effect_on_claim_status`.

### L2 — Full matrix

**When:** deep due diligence, legal, geopolitical critical.

**Artifact:** full `contradiction-matrix.json` conforming to rewritten **non-stub** schema (implementation replaces current placeholder).

## Optional vs required logic

`contradictions-lite.json` is **optional only if**:

- scan performed AND `high_severity_detected == false` AND no medium severity unsettled conflicts.

Otherwise artifact becomes **required** — V4 blocks if missing.
