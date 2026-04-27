# Reliability Hardening Protocol

Invariant (verbatim):
```text
Context is disposable. Files are memory. State machine is law. Draft is not final. No source, no claim. No validation, no checkpoint. Pending queue means no stop.
```

## Required mechanisms
- **Single source of truth** — `runtime-state.json`, `queue.json`, `artifact-manifest.json`, item `stage` files, artifacts on disk; reload before major steps.
- **Pre/postconditions** per stage; no advance on failed postcondition.
- **Loop guards** — every loop has max iterations; see contract `loop_guards`.
- **No-progress** — if N steps without artifact/state progress, mark retryable or blocked per policy.
- **Context snapshots** — `items/<slug>/context-snapshot.md` after major stages.
- **No silent reset** — resume unless `FORCE_REBUILD` + explicit user request.
- **Idempotent writes** — write to temp, validate, rename; keep `final.previous` when replacing finals.
- **Source-limited mode** — no fabrication; downrank confidence; list gaps.
- **Anti-drift** — re-read `runtime-contract.json` and `SKILL` constraints at each item boundary.

## Watchdog
`logs/watchdog.md` (optional) or entries in `activity-history.html` for repeated failures / stuck stages.
