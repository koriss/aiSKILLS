# v18.3.2 Modularization Roadmap (historical note)

Superseded in-tree: implementation lives under `runtime/*_impl.py`, `scripts/rfo_runtime_core.py`, `scripts/validate_runtime_artifacts.py`, and [`contracts/core-boundary-contract.json`](../../contracts/core-boundary-contract.json). The old monolith entry `scripts/rfo_v18_core.py` has been removed.

## Finding (archival)

Historical risk was a single-script god module coupling adapter, orchestration, worker, outbox, validation, harness, rendering, and packaging.

## Hotfix scope

v18.3.2 does not pretend that the god module is fully refactored. It adds:

```text
runtime/adapter.py
runtime/worker.py
runtime/outbox.py
runtime/validation.py
runtime/packaging.py
~~runtime/smoke.py~~ removed
contracts/core-boundary-contract.json
```

These files define bounded component ownership and compatibility wrappers. A future v18.4/v19 should move implementation from `rfo_v18_core.py` into these modules behind stable contracts.

## Target boundaries

```text
adapter: interface request normalization and job creation
worker: job claim, work-unit lifecycle, runtime execution
outbox: provider payloads, delivery ack, attachment ledger
validation: machine-readable gates, no HTML string heuristics as source of truth
packaging: canonical package builder and manifest
smoke/failure: harness only, never production acceptance
```

## Validation source-of-truth rule

HTML may be checked for render hygiene, but pass/fail gates must come from JSON artifacts and schemas, not string matching in rendered HTML.
