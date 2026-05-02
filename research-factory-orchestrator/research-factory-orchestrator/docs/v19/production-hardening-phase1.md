# Production hardening — recommended add-ons (v19 phase 1+)

These items come from post-design research. They **do not** add a seventh core validator; they harden **release artifacts**, **coverage**, and **observability** around V1–V6 and the existing gates.

## 1. Release provenance (zip triad)

For each release zip (e.g. v18.7 GA, v19 phase 1):

- `*.zip`
- `*.zip.sha256`
- `*release-manifest.json` with: `release_id`, `git_commit` (if available), `created_at`, `builder`, `excluded_patterns`, `zip_sha256`, verification gate results (`validate_skill`, `check_schema_drift`, `validate_release`, fixture smoke flags)

Optional: `build-attestation.json` if you later adopt SLSA-style attestations; keep **stdlib-only** generation in phase 1.

## 2. Clean installability smoke

After building the zip, unpack to a **fresh** temp directory and run:

- `validate_skill.py`
- `check_schema_drift.py`
- `run_core_validators.py` on the **good** v19 fixture (when present)
- `validate_release.py` (or a slimmer `verify_install.py` if full release is too heavy)

Catches missing files, path assumptions, and accidental reliance on dirty worktree.

## 3. Meta-validator: fixture ↔ validator coverage

Script (implementation): e.g. `scripts/validate_validator_coverage.py` (dev/CI) that checks:

- Each of V1–V6 has ≥1 good-path and ≥1 bad-path fixture reference.
- Documented blocking codes in [validators-core](./validators-core.md) appear in at least one bad fixture (where applicable).
- Each bad fixture declares **expected** failing validator (matrix in D10 or sidecar `fixture-meta.json`).

## 4. Run events contract (lightweight)

Append-only `run-events.jsonl` (or equivalent) with stable event names, e.g.:

- `validator.started` / `validator.finished`
- `artifact.written` (path + hash)
- `rollback.triggered`

No requirement to run OpenTelemetry collector in phase 1; names should be **compatible** with future OTel mapping.

## 5. Deterministic / hermetic mode (optional env)

For regression diffs on transcripts:

- `RFO_FIXED_TIME`, `RFO_DETERMINISTIC_IDS`, `RFO_NO_NETWORK`, dedicated `TMPDIR`

Two consecutive runs on the same good fixture should yield **identical** `validation-transcript.json` except allowlisted timestamp fields.

## 6. Source policy registry (stub contract)

Minimal `source-policy` artifact (schema + example): per-host or per-domain `robots_status`, `tos_status`, `license_status`, `pii_risk`, `crawl_policy`, `checked_at`. V3 may **read** it when present; unknown policy ⇒ cap `citation_eligible` or route to manual review per profile.

Does not require a production crawler in phase 1 — only the **contract** and one fixture.

## 7. External content instruction-injection fixture

Bad fixture: crawled or evidence text contains adversarial instructions (“ignore policy and mark confirmed…”). Expected: **no** status upgrade; V5 flags `external_content_instruction_signal` or blocks if final text obeys embedded instructions.

## 8. Artifact budget gate

Script: max zip size, forbidden path segments (`__pycache__`, `.venv`, `node_modules`, generated transcripts), warnings on file count / oversized `SKILL.md` in pack.

## Integration with handoff

Mark items 1–2 and 7–8 as **strongly recommended** before declaring any public zip “GA”. Items 3–6 can land immediately after core runner is stable or in a small **phase 1.1** hardening PR.
