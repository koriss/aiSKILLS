# v18.3.2 Modularization Roadmap

## Finding

`rfo_v18_core.py` is currently a compatibility god module: adapter, orchestration, worker, outbox, validation, smoke/failure harness, rendering, and packaging live in one file. This is a high architectural risk.

## Hotfix scope

v18.3.2 does not pretend that the god module is fully refactored. It adds:

```text
runtime/adapter.py
runtime/worker.py
runtime/outbox.py
runtime/validation.py
runtime/packaging.py
runtime/smoke.py
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
