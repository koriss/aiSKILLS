# ADR-015 — Runtime truth restoration (v19.2.0)

## Status

Accepted — implemented across Phases 2–6 + integration smokes (`_smoke_v19_2_*`).

## Context

v19 validators assumed artifacts that runtime did not always emit (legacy-shaped
fields, rollback masking pristine passes, collection/coverage vocabulary drift).
This produced **green smokes with false production posture**.

## Decision

1. **Single emission path** — `runtime/worker_impl.py` + collectors write v19
   root artifacts; dual-layout mirrors are explicit (`runtime/render.py`,
   `runtime/collector.py`).
2. **No silent rollback green** — `runtime/smoke_impl.py` rollback closure cannot
   mask a pristine `overall_pass=true` path (operating discipline **0c**).
3. **Work-unit + collection truth** — executors and collectors write evidence-backed
   JSON; guards registered in `contracts/validator-registry.json`.
4. **Subprocess hardening** — `scripts/validate_release.py` uses new session +
   `killpg` on POSIX timeouts (T8.1).
5. **Failure-code registry** — `failure-corpus/index-v19.json` carries `severity:
   "meta"` rows for new truth-class codes without breaking fixture reproduction
   checks (`validate_validator_coverage.py` only enforces `severity == "error"`
   rows with real fixture paths).

## Consequences

- Release gate time increases (extra smokes + Telegram traces + advisory stub).
