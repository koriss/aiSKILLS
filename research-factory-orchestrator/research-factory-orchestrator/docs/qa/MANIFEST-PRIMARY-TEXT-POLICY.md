# Manifest `primary_text` policy (reference)

This policy lives in the skill repo so deployment layers can copy it verbatim.

## Goal

Define safe, deterministic usage of `result-manifest.json.primary_text` for user-facing delivery previews without overstating delivery proof.

## Rules

1. `primary_text` is a **preview**, not delivery proof.
2. Delivery layers MAY send `primary_text` first when:
   - manifest parsing succeeds,
   - `status` is `ok` or `partial`,
   - artifact list is still attached/processed according to host policy.
3. Delivery layers MUST NOT claim “all artifacts delivered” based on `primary_text` alone.
4. If artifact attachment fails, report attachment failure explicitly; do not silently substitute `primary_text` as a success path.
5. Keep this policy aligned with `schemas/skill-result.schema.json` and ADR-016/ADR-019 boundaries.

## Suggested check

- Compare final user-visible message metadata with:
  - `result-manifest.json.status`
  - attachment outcomes
  - gateway/channel audit record

