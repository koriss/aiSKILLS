# RFO operating discipline (v19.0.4)

0. **v19.0.4 boundary refresh** — `contracts/core-boundary-contract.json` @ 19.0.4 documents `runtime/*_impl.py` + `runtime/cli.py` + deprecated `runtime/impl.py` shim; release `REQUIRED_GATES` adds `smoke_cli_v19` + `_smoke_corrupt_render`; proof transcript policy: `docs/adr/ADR-011-release-validation-transcript.md`; see `docs/release-notes/v19.0.4.md`.

1. **v19.0.3 closure pass** — fail-closed rollback uses `minimal_valid` + physical rollback stub; release `REQUIRED_GATES` + B4 transcript self-attestation; dual Telegram smokes (v18 + `RFO_V19_PROFILE=mvr`); see `docs/release-notes/v19.0.3.md` (and `v19.0.2.md` for prior patch notes).

2. **One bug class → one fix → one negative test → one proof** in the failure-corpus or `scripts/test_*.py`.
3. **No new surface area** until current invariants have a failing fixture that turns green after the fix.
4. **Delivery truth**: never claim user-visible delivery unless `publish_allowed` + `delivery_claim_allowed` agree with gates and provider capabilities.
5. **Schema drift**: bump `runtime/version.json` when changing `enum` / `required` / `additionalProperties` on critical manifests.
6. **Every gate change MUST cite** a referenced source (arXiv / IETF draft / agency-agents agent definition) in the PR / release note entry.
7. **Validation fail-closed**: if `validation-transcript.status` is `fail`, rollback optimistic delivery claims (`delivery-manifest`, `final-answer-gate`, `runtime-status`) — never leave “delivered” artifacts inconsistent with validation failure.
8. **Release report honesty**: do not mark release steps as `pass` without a fresh `release-validation-transcript.json` produced by `scripts/validate_release.py` with matching step fingerprints.
9. **Logical consistency (v18.7)**: after validation, `scripts/validate_logical_consistency.py` must pass on the run-dir; `run.json` records `mode`, `requested_mode`, and `normalized_from` when the effective mode differs from the operator request; production runs must not leave `feature-truth-matrix.json` features in `stub`/`missing`/`scaffold`.

10. **Pragmatic Rigor core (v19 phase 1)**: optional `RFO_V19_PROFILE` (`mvr`, `full-rigor`, `propaganda-io`, `book-verification`) switches `runtime/validate_impl.validate` to `scripts/run_core_validators.py` (V1–V6) instead of the legacy DAG; frozen contracts live under `schemas/core/`; operator summary in `SKILL-core.md`.
