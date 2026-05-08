# RFO operating discipline (v19.3.0)

0c. **Runtime truth vs rollback** — `cmd_run` emission + artifact layout are the single source of truth; fail-closed rollback must **not** mask inconsistent “green” manifests.

0a. **v19.1.0 verification + replay** — advisory channels (`blinded_checker`, `typed_grounding`, optional `judge_council`) + `run-events.jsonl` trajectory contract; deterministic knobs `RFO_FIXED_TIME` / `RFO_DETERMINISTIC_IDS` / `RFO_NO_NETWORK`; release zip triad + coverage-meta per `docs/adr/ADR-012-multi-agent-verification.md` and `docs/adr/ADR-013-replayable-evidence.md`; see `docs/release-notes/v19.1.md`.

0. **v19.3 boundary** — `contracts/core-boundary-contract.json` documents `runtime/*_impl.py` + `runtime/cli.py`; entry façade `scripts/rfo_runtime_core.py`. Release `REQUIRED_GATES` include `artifact_execute_v19_3` + `validate_artifact_release`; see `docs/release-notes/v19.3.md` and `docs/adr/ADR-011-release-validation-transcript.md`.

1. **Classification-driven publish policy** — `contracts/publish-policy.json` applies `non_production_publish_modes` using effective mode from **`run-mode-classification.json`** (Outbox computes; falls back to `run.json.mode`). Delivery manifests use **`checks`**, never legacy `gates`, alongside `final-answer-gate.json.checks`.

2. **One bug class → one fix → one negative test → one proof** in the failure-corpus or `scripts/test_*.py`.
3. **No new surface area** until current invariants have a failing fixture that turns green after the fix.
4. **Delivery truth**: never claim user-visible delivery unless `publish_allowed` + `delivery_claim_allowed` agree with **`checks`** in manifests and provider capabilities.
5. **Schema drift**: bump `runtime/version.json` when changing `enum` / `required` / `additionalProperties` on critical manifests.
6. **Every gate change MUST cite** a referenced source (arXiv / IETF draft / agency-agents agent definition) in the PR / release note entry.
7. **Validation fail-closed**: if `validation-transcript.status` is `fail`, rollback optimistic delivery claims (`delivery-manifest`, `final-answer-gate`, `runtime-status`) — never leave “delivered” artifacts inconsistent with validation failure.
8. **Release report honesty**: optionally compare `scripts/validate_release_report.py --transcript …` with a Markdown report (`RFO_RELEASE_REPORT_PATH`). `release-validation-transcript.json` is generated locally by `validate_release.py` and is gitignored unless you deliberately commit CI output.
9. **Logical consistency**: after validation, `scripts/validate_logical_consistency.py` must pass on the run-dir; `run.json` records `mode`, `requested_mode`, and `normalized_from` when the effective mode differs from the operator request; production runs must not leave `feature-truth-matrix.json` features in `stub`/`missing`/`scaffold`.

10. **Pragmatic Rigor core**: optional `RFO_V19_PROFILE` (`mvr`, `full-rigor`, `propaganda-io`, `book-verification`) switches `runtime/validate_impl.validate` to `scripts/run_core_validators.py` (V1–V6); frozen contracts live under `schemas/core/`; operator summary in `SKILL-core.md`.
