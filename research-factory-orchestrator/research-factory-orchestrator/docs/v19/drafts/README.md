# `docs/v19/drafts/` — FROZEN

**Do not edit files in this directory.** They are historical design-phase snapshots from v19 Pragmatic Rigor planning.

## Single source of truth (live)

- Schemas: `schemas/core/`
- Validation profiles: `validation-profiles/`
- Core validators: `validators/core/`
- Runner: `scripts/run_core_validators.py`

Material from drafts was merged into the paths above. Any schema or profile change must be made **only** in those live locations, then reflected in tests and `scripts/check_schema_drift.py` fingerprints as needed.
