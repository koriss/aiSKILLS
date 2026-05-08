# Phase 11 purge summary (commit #1)

- Branch: `cleanup/v19-only-version-purge`
- Baseline inventory: `00-inventory.md` (`v1[0-8]` baseline was 440 hits in full repo scan).
- Purge groups completed:
  - legacy runtime compatibility layer removed (`runtime/legacy_compat.py`, legacy validators/contracts).
  - version-named corpora/examples/policies removed (`examples/v14-v17`, `references/v14-v17`, `tests/v14-regression-corpus`, legacy failure-corpus overlays).
  - SKILL docs rewritten to v19-only surface (`SKILL.md`, `SKILL-core.md`).
  - scripts/runtime/contracts/docs cleaned from active `<19` references.
  - v19.2.x smoke extras removed (`_smoke_v19_2_1_repro_after_fix.py`, `_smoke_v19_2_phase5_matrix.py`) and references cleaned.

- Risk notes:
  - `release-validation-transcript.json` still reports non-gating failures in broader release suite (`failure_corpus`, `validate_logical_consistency`) and was intentionally not force-fixed in purge commit scope.
  - one intentional `<19` token remains in stale-token denylist (`scripts/validate_generator_hygiene.py`) for hygiene detection logic.

- Phase 10 checks before commit:
  - `validate_skill`: pass
  - `rfo_runtime_core.py smoke`: pass
  - `_smoke_v19_2_integration`: pass
