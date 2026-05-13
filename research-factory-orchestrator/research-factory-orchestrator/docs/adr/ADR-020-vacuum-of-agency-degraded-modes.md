# ADR-020 — Vacuum of agency and degraded modes (RFO vs host)

## Status

Accepted (design note, skill repo).

## Context

RFO is designed as **deterministic compute**: queue, lease, manifests, validators, artifact-only stdout contracts. The host gateway optimizes for **user responsiveness**: avoid empty chat when a subprocess is slow, killed, or blocked on `lease_present`.

When those goals conflict, the LLM is pushed toward **plain subagent / chat research** — a path that does not produce the same machine-checkable run-dir. Operators then see two incompatible “truths” (memory Markdown vs `final-answer-gate.json`).

## Decision

1. **Canonical prod entrypoint** for relay+queue is **`scripts/rfo_execute.py`** (delegates to `run_rfo_with_web_search.py`); **`run_rfo_full_research.py`** is **not** an operator entrypoint (grave marker → **`rfo_execute.py`**, exit **2**).
2. **Degraded modes must stay in-contract** where possible: expose bridge/worker state (`bridge.worker_poll`, lease runbook) instead of silently switching research genre under the same slash.
3. **Out-of-contract relief** is allowed only via **explicit** separate commands or host UX — not by re-labeling plain subagent output as RFO completion.

## Consequences

- Host owners must align **timeouts** with bridge worker env (see `docs/operators/openclaw-gateway-rfo-notes.md`).
- `search-primary` and similar **harness** profiles may intentionally omit deep contradiction scans; dossier profile owns that depth (`docs/runtime-paths.md`).
