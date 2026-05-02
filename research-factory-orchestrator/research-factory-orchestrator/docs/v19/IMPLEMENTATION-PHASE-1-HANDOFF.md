# RFO v19 — Implementation phase 1 (handoff)

**Prerequisite:** design sign-off using `DESIGN-REVIEW.md`.

**Parallel:** complete v18.7 (production-mode + `validate_logical_consistency.py`) independently; do not block on v19.

## Phase 1 scope (recommended order)

1. **Copy frozen drafts** from `docs/v19/drafts/schemas/core/` → `schemas/core/` (or equivalent) + register in packaging.
2. **Land fixtures** per `failure-fixtures.md` under `tests/fixtures/v19/` **before** merging validator bodies.
3. **Implement six validators** exactly as `validators-core.md` — stdlib-only runtime contour.
4. **Implement `scripts/run_core_validators.py`** per `run-core-validators-spec.md`.
5. **Wire profiles** from `docs/v19/drafts/validation-profiles/` → `validation-profiles/` at repo root (or keep under docs if skill packaging requires).
6. **Replace** stub `schemas/contradiction-matrix.schema.json` with production version derived from `drafts/schemas/heavy/contradiction-matrix.schema.json`.
7. **Migration tooling:** script to map old validator invocations → new runner (shim period).
8. **Collapse SKILL** to `SKILL-core.md` + move overlays to `legacy/`.
9. **Smoke + release validation** updated to call new runner for MVR profile on golden run-dir.

## Explicit non-goals for phase 1

- No deletion of orphan validators yet (move to `legacy/scripts/` optionally).
- No KB repackaging (separate ADR).
- No auto-profile keyword escalation without structured signals.

## Acceptance (phase 1 exit)

- All fixtures green/red as expected against six validators.
- MVR profile run completes on reference run-dir in <N seconds (set budget during impl).
- Release proof uses deduped `run_id` rules + version alignment (carry forward v18.5.1 fixes).

## Recommended hardening (after research — see D15)

Not required for the **narrow** definition of phase 1 (six validators + runner + fixtures), but **strongly recommended** before declaring any distributable workspace zip “production ready”:

1. **Release triad**: `*.zip.sha256`, `release-manifest.json` (gates, commit-ish, exclusions), optional `build-attestation.json`.
2. **Clean unzip smoke**: run validator/skill/release checks from `/tmp/` after unpacking the zip — catches implicit paths.
3. **Meta-validator**: `validate_validator_coverage.py` — each V good+bad fixtures; blocking codes exercised.
4. **Run events**: optional `run-events.jsonl` with stable event vocabulary (maps to observability later).
5. **Deterministic replay env** for transcript hash stability regression tests.
6. **`source-policy` stub**: schema + example JSON for per-domain crawl/TOS posture (feeds V3 when present).
7. **Injection bad fixture**: crawled “ignore instructions” text must not elevate claim status (V5).
8. **`check_artifact_budget.py`**: max zip size, forbidden cache paths, SKILL size warnings.

Detail: [`docs/v19/production-hardening-phase1.md`](./production-hardening-phase1.md).

## Doc index

Full design packet: `docs/v19/README.md`.
