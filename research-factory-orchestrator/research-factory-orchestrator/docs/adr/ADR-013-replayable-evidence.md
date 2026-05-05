# ADR-013 — Replayable evidence & release proof (v19.1)

## Status

Accepted — implemented in v19.1.0.

## Context

“Temperature = 0” is insufficient for reproducible audits. Incidents in production ML systems show the value of **trajectory-level** evaluation and **artifact-attested** releases (replay labels, pass@k on noisy traces, durable run logs). RFO already batches validation; v19.1 adds **deterministic knobs**, **append-only run events**, **trajectory smokes**, and **release zip triad + clean-install smoke**.

## Decision

1. **B1 — Deterministic mode** — `RFO_FIXED_TIME`, `RFO_DETERMINISTIC_IDS`, `RFO_ID_SALT`, `RFO_NO_NETWORK` (see `runtime/util.py`, `runtime/validate_impl.py`, `runtime/smoke_impl.py`).
2. **B2 — Deterministic replay smoke** — `scripts/_smoke_deterministic_replay.py` runs `validate()` twice on `good/mvr_minimal_valid` with identical B1 env; normalized `validation-transcript.json` must match (`DETERMINISTIC-DRIFT` on failure).
3. **B3 — `run-events.jsonl`** — OTel-style names: `validator.started`, `validator.finished`, `artifact.written`, `rollback.triggered` from `run_core_validators.py` and `_fail_closed_rollback`.
4. **B4 — Trajectory smoke** — `scripts/_smoke_trajectory_v19.py` asserts V1→V6 start/finish pairing on pass path and `rollback.triggered` on a controlled fail path (`TRAJECTORY-SKIP` on failure).
5. **C1 — Release zip triad** — `validate_release.py` emits `release-artifacts/*.zip`, `*.zip.sha256`, `release-manifest.json` (stdlib `zipfile` + `hashlib`; `git rev-parse` soft-fail).
6. **C2 — Clean-install smoke** — `scripts/_smoke_clean_install.py` unzips the release zip to a temp tree and runs `validate_skill`, `check_schema_drift`, and `run_core_validators` on `good/mvr_minimal_valid` from that tree.
7. **C3 — Coverage meta** — `scripts/validate_validator_coverage.py` enforces fixture matrix + failure-corpus **error** code reproduction; emits `coverage-report.json` (`COVERAGE-GAP` on failure).

## Citations (external framing)

- **Trajectory / noise-aware eval** — industry practice of evaluating sequences, not only terminal answers (e.g. “Bits AI”-style incident replay narratives).
- **Deterministic replay** — product guidance stressing logged non-deterministic sources beyond RNG seeds (Tianpan-style replay writeups; LangGraph-style durable task idempotency as *analogy*, not an in-scope engine change for v19.1).

## Consequences

- Release CI time increases (extra smokes + coverage meta + zip + clean install).
- `release-artifacts/` is gitignored content-wise but may appear locally after `validate_release`.
