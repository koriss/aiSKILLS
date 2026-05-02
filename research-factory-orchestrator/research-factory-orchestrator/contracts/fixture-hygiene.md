# v19 Fixture Hygiene Contract

Single source of truth for `tests/fixtures/v19/{good,bad}/*` and `tests/fixtures/v19/release_bad/*`.

## Allowed inputs in `tests/fixtures/v19/{good,bad}/*`

- `run.json`
- `sources.json` (or `sources/sources.json` if the runner resolves it)
- `evidence-cards.json`
- `claims-registry.json`
- `final-answer-gate.json`
- `delivery-manifest.json`
- `contradictions-lite.json` (only when the scenario requires contradiction scan)
- `report/full-report.html` (optional)
- `observability-events.jsonl` (optional, if used by a scenario)
- `expected.json` (**mandatory** for every fixture)

## Forbidden in `tests/fixtures/v19/{good,bad}/*` (generated outputs)

These are written only by runners or runtime — **must not** appear in fixture trees:

- `validation-transcript.json` — written only by `scripts/run_core_validators.py`
- `validation-profile-used.json` — written only by `scripts/run_core_validators.py`
- `runtime-status.json` — written by runtime
- `release-validation-transcript.json` — written by `scripts/validate_release.py`

`scripts/validate_v19_fixture_suite.py` **MUST** fail with `FIXTURE-HYGIENE-VIOLATION` if any forbidden file is present under `good/` or `bad/`.

## `release_bad/` fixtures

`tests/fixtures/v19/release_bad/*` are **not** run-dir validator fixtures. They are exercised by `scripts/validate_v19_release_bad_suite.py` via `validate_release_report.py` (and related release checks). Same hygiene: no pre-baked `validation-transcript.json` unless the release checker explicitly documents it as input (default: forbidden).

## `expected.json` schema (validator suite)

Used by `scripts/validate_v19_fixture_suite.py` for `good/` and `bad/`:

```json
{
  "expected_profile": "mvr | full-rigor | propaganda-io | book-verification",
  "expected_rc": 0,
  "expected_validator": "validate_traceability",
  "expected_issue_codes": ["missing_evidence_card"],
  "allow_prior_fail": false,
  "rationale": "human-readable explanation"
}
```

- For `expected_rc: 0`, omit `expected_validator` and `expected_issue_codes` or use empty array as documented by the suite runner.
- For `expected_rc: 1`, `expected_validator` is the validator id (script stem) that must be the **first** failing validator unless `allow_prior_fail` is true.
- `allow_prior_fail` (default `false`): when false, the first validator with `status=fail` must equal `expected_validator`, and all `expected_issue_codes` must appear in that validator's issues.

## `expected.json` schema (release_bad suite)

Used by `scripts/validate_v19_release_bad_suite.py`:

```json
{
  "expected_rc": 1,
  "expected_checker": "validate_release_report",
  "expected_issue_codes": ["release_pass_without_transcript"],
  "rationale": "..."
}
```

## Version

Contract applies from RFO **19.0.3** onward (v19.0.2 baseline retained in historical fixtures where noted).
