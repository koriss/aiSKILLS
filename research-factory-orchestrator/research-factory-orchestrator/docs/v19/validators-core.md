# D2 — Six core validator specifications (v19)

## Global contract

| Property | Value |
|----------|--------|
| Language | Python 3, **stdlib only** in runtime contour (no `jq`, no network, no pandas; `jsonschema` optional **dev-only** if team chooses — default is stdlib `json` + hand-validators) |
| CLI | `--run-dir <path>` required |
| Exit code | `0` iff `passed==true` and no blocking issues |
| Crash / uncaught exception | **blocking failure** (emit synthetic result JSON + non-zero exit) |
| Missing required artifact | **blocking failure** (schema phase or dedicated check) |

## Unified result object (stdout JSON, one object per invocation)

```json
{
  "validator_id": "validate_traceability",
  "schema_version": "v19.0",
  "passed": false,
  "blocking": true,
  "issues": [],
  "warnings": [],
  "summary": "short human-readable"
}
```

- `issues[]`: `{ "code", "severity": "error"|"warning", "path", "detail", "artifact" }`
- `blocking`: true if any error is blocking per profile rules.

---

## V1 — `validate_artifact_schema`

**Purpose:** Fail-fast structural validation of **core artifacts** present under `run_dir`.

**Inputs:** `--run-dir`, optional `--profile` (for which optional artifacts are required).

**Core files (always required when run claims research-complete):**

- `sources.json` (or agreed path — see D7)
- `evidence-cards.json`
- `claims-registry.json`
- `final-answer-gate.json`
- `delivery-manifest.json`
- `validation-transcript.json`

**Optional by profile / state:**

- `contradictions-lite.json` — required iff profile or scan says conflicts exist (see D5, V4).

**Blocking:** parse error, missing required file, `schema_version` mismatch against supported set, `additionalProperties` violation (when schema enforcement is on).

**Replaces / absorbs (implementation mapping):** loose one-off “file exists” checks; first gate before all others.

---

## V2 — `validate_traceability` (Sacred Path)

**Purpose:** Enforce:

`final_sentence → claim_id → evidence_card_id → source_id → (source record exists)`

**Mechanical rules:**

1. Every **claim** has `≥1` evidence card reference.
2. Every **evidence card** references `≥1` existing `source_id`.
3. Every evidence card has non-empty **excerpt or extracted_fact** (field names per D7 schema).
4. No orphan evidence cards referenced only from deleted claims without tombstone policy (implementation).
5. `support_set[]` on each claim (see D11) lists `{ source_id, evidence_card_id, role_for_claim }`; roles `primary_support` and `corroboration` are the only roles that count toward thresholds in V3/V4.

**Blocking:** any break in chain.

**Replaces / absorbs:** ad-hoc trace scripts; partial Grok-style traceability that skipped `sources.json`.

---

## V3 — `validate_source_quality`

**Purpose:** Multidimensional source assessment + **claim-type-aware** thresholds.

**Rules:**

- No single numeric “trust score” as authority; dimensions are **categorical enums** (see D3, D11).
- **Threshold counting:** only `primary_support` + `corroboration` entries in `support_set` participate. `context`, `lead`, `opposition` never upgrade strength.
- **Independence:** `effective_independent_support_count` = count of **distinct** `canonical_origin_id` (fallback: normalized URL / document hash) among support-set sources — not raw `len(source_ids)`.
- **Citation eligibility:** `citation_eligible` requires retrievable locator (`url` **or** `document_path` **or** `archival_locator`) — sources without locator cannot be sole basis for `confirmed_fact` (warning or block per profile).
- **KB boundary:** KB identifiers must not appear as `source_id` for factual claims (see D6, propaganda profile).

**Blocking:** profile-dependent; MVR may warn on weak sole-source for sensitive types; Full blocks.

---

## V4 — `validate_claim_status`

**Purpose:** Consolidate claim lifecycle, status caps, lite contradiction obligations, snippet/lead rules.

**Includes:**

- `confirmed_fact` must satisfy claim-type policy (D3, D11).
- `snippet_only` / `lead_only` cannot back `confirmed_fact`.
- **Contradictions-lite:** if medium/high conflict between support-set sources for same claim → `contradictions-lite.json` **required** and must contain resolving or `unresolved` with severity.
- **L0 scan metadata** propagated to gate (from artifacts): if profile requires scan and `high_severity_detected` is `unknown` → block.
- Laundering / circular corroboration: basic detection (same origin, duplicate URLs) — detailed graph = heavy module.

**Blocking:** status cap violation, required contradiction artifact missing, unresolved critical contradiction (profile).

**Replaces / absorbs:** `validate_snippet_only_not_confirmed`, parts of claim-source-fit, lightweight contradiction checks.

---

## V5 — `validate_final_answer`

**Purpose:** Final text vs registry: no new facts, calibration, overclaiming.

**`overconfidence_risk` buckets (D4):**

- **blocking[]** — any item here ⇒ `passed=false` for V5.
- **warnings[]** — non-blocking; must appear in transcript.

Examples of **blocking**: `new_fact_without_claim_id`, `absolute_statement_without_high_confidence_backing`, `causal_language_without_causal_evidence`, `confirmed_with_non_high_confidence`, `forecast_scenario_written_as_fact`.

**Replaces / absorbs:** `validate_summary_no_new_facts`, parts of adversarial/final checks.

---

## V6 — `validate_delivery_truth`

**Purpose:** Minimal **operational safety** (v18.5.1 lessons preserved).

**Split claims (mandatory fields in manifest — see D6):**

- `artifact_ready_claim_allowed`
- `external_delivery_claim_allowed`
- `stub_delivery_disclosure_required`

**Invariant:** `provider_pass` / adapter completion **must not** imply `external_delivery_claim_allowed`.

**Checks:**

1. Claimed artifacts exist and hashes match manifest.
2. `provider_ack_id` present **or** explicit stub with disclosure.
3. Ack namespace matches provider (`cli` → local namespace; never external).
4. `provider=cli` ⇒ `real_external_delivery=false` always.
5. No absolute local paths in **any user-visible artifact** list (not only `chat/*.txt` — see D6).
6. Rollback completeness: if validation fails, failed state must be **explicit** in artifacts (no silent absence).

**Replaces / absorbs:** `validate_stub_delivery_not_external`, `validate_no_local_paths_in_chat` (expanded scope), `validate_no_delivery_after_validation_fail` coordination.

---

## Order of execution

1. V1 → V2 → V3 → V4 → V5 → V6 (strict pipeline).
2. Any blocking failure in an earlier stage may short-circuit later stages **but** transcript must record skipped stages as `skipped_due_to_prior_failure`.
