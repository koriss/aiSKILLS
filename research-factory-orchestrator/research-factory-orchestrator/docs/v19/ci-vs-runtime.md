# D9 — CI vs runtime separation

## Runtime (OpenClaw / portable skill contour)

**Must run offline** on a run directory with:

- Python 3 stdlib
- Six core validator scripts + `run_core_validators.py` (see `run-core-validators-spec.md`)
- Core JSON schemas (frozen copies under `schemas/core/` in implementation)

**Must not require:**

- `jq`
- GitHub Actions
- Network access
- `pandas`, `numpy`, heavy ML stack
- `jsonschema` **unless** explicitly vendored — default decision: **avoid**; use handwritten checks + schema JSON as spec reference

## Dev / release contour (repository)

May include:

- `.github/workflows/*`
- `pre-commit` hooks calling validators on synthetic fixtures
- `validate_release.py` / `validate_release_report.py` style orchestration
- Optional `jsonschema` CLI for CI diffing

## Helper: `check_validation_pass.py` (implementation)

Pure Python replacement for shell `jq` one-liners:

- Reads `validation-transcript.json`
- Exits non-zero if `overall_pass != true`
- Prints concise summary for humans

## Transcript contract

CI must consume the **same** `validation-transcript.json` schema as runtime (draft: `drafts/schemas/core/validation-transcript.schema.json`).
