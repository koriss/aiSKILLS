# RFO remaining plan (post gap-closure pass)

This file tracks only items that remain after the current implementation cycle.
It is intentionally short and executable.

## Scope

- Repository: `research-factory-orchestrator/research-factory-orchestrator`
- Development, deployment prep, and test/reference implementations are all maintained **here**; later transport to another repo is an ops step, not a blocker.

## Remaining items

### R1 — Host parser hardening reference (implemented here first)
- **id:** `local-host-handoff-scan-reference`
- **status:** completed
- **what:** Keep canonical parser logic in this repo: scan non-empty stdout lines for `__RFO_SKILL_AGENT_HANDOFF__=` and take the last valid capsule instead of trusting only the final line.
- **notes:** Also documented by `docs/adr/ADR-019-host-handoff-stdout-scanning.md`; downstream repos should copy from this reference.

### R2 — Manifest `primary_text` delivery policy (defined here)
- **id:** `local-manifest-primary-delivery-policy`
- **status:** completed
- **what:** Define and document policy for when delivery layers should prefer `result-manifest.json.primary_text` before attachments, aligned with `skill-result` schema.
- **notes:** Runtime remains compute-only; policy and reference checks still live in this repo for portability.

### R3 — Full-doc neutrality sweep (deep pass)
- **id:** `repo-neutrality-full-sweep`
- **status:** completed
- **what:** Expand neutrality pass from live docs to all historical/diagnostic/release docs where vendor or channel labels remain.
- **acceptance:**
  - Run `rg` over markdown/doc trees.
  - Keep only allowed residuals:
    - historical ZIP filenames in archive matrix,
    - compatibility filename references to `verify_openclaw_run.py`,
    - explicitly frozen historical notes.
  - Update `docs/qa/NEUTRALITY-SCAN.md` with final residual set.

### R4 — Legacy verifier name cleanup policy
- **id:** `repo-verifier-compat-window-closeout`
- **status:** completed
- **what:** Decide end-of-life window for `scripts/verify_openclaw_run.py` wrapper and remove compatibility mentions when safe.
- **acceptance:**
  - Consumers switched to `verify_skill_run_claims.py`.
  - CHANGELOG note for wrapper retirement.
  - `required_scripts` adjusted if wrapper removed.

### R5 — Queue starvation guard in worker loop
- **id:** `repo-worker-queue-starvation-guard`
- **status:** completed
- **risk class:** high (liveness / throughput)
- **problem:** `runtime/worker_impl.py` claims only the first pending job and, on repeated failure/timeout, pushes the same job back to `pending` head behavior. A poison job can starve following jobs.
- **what:** Add bounded retry/backoff metadata per job (`queue_attempts`, `last_failure_at`) and optional skip/park mechanism for hot-failing jobs.
- **acceptance:** failing job no longer blocks unrelated jobs in `queue/pending`.

### R6 — Bridge worker retry branch can over-report readiness in best-effort
- **id:** `repo-bridge-best-effort-truth-tightening`
- **status:** completed
- **risk class:** high (truth boundary)
- **problem:** in `scripts/run_rfo_with_web_search.py`, `--best-effort-continue` may proceed after worker hard failure and still attempt render/handoff if `run_dir` exists.
- **what:** enforce stricter artifact sanity gate before handoff in best-effort mode (`run.json`, `runtime-status`, required report/chat artifacts existence and freshness).
- **acceptance:** no handoff emitted from incomplete worker runs unless explicitly marked degraded with machine-readable reason.

### R7 — Outbox exception swallowing hides root causes
- **id:** `repo-outbox-error-surfacing`
- **status:** completed
- **risk class:** medium (diagnostics)
- **problem:** several broad `except Exception: pass` in `runtime/outbox_impl.py` and `runtime/worker_impl.py` suppress context, making delivery regressions hard to triage.
- **what:** replace silent passes with structured `runtime/errors.jsonl` events and narrow exception scopes where feasible.
- **acceptance:** every suppressed failure path produces a traceable machine-readable error record.

### R8 — Release validator transcript write duplication / clarity
- **id:** `repo-validate-release-transcript-cleanup`
- **status:** completed
- **risk class:** low-medium (maintainability)
- **problem:** `scripts/validate_release.py` writes transcript repeatedly with duplicated blocks; harder to audit and reason about ordering.
- **what:** refactor transcript writes into one helper (`persist_transcript`), remove duplicate write blocks, preserve behavior.
- **acceptance:** same output schema, fewer duplicated code paths, unchanged gate semantics.

### R9 — Parser fragility for multiline JSON stdout
- **id:** `repo-bridge-stdout-json-parse-hardening`
- **status:** completed
- **risk class:** medium (integration robustness)
- **problem:** `_parse_stdout_json_object` in `scripts/run_rfo_with_web_search.py` assumes either full JSON text or single-line `{...}`; multiline pretty-printed objects mixed with logs can be missed.
- **what:** adopt robust extraction strategy consistent with `scripts/parse_handoff_stdout_reference.py` patterns (scan candidates + incremental JSON parse).
- **acceptance:** adapter/worker stdout parsing succeeds with multiline JSON plus surrounding logs.

### R10 — Test invocation guard for discovery consistency
- **id:** `repo-test-discovery-command-guard`
- **status:** completed
- **risk class:** low (DX / false confidence)
- **problem:** plain `python3 -m unittest` may report `Ran 0 tests` depending on cwd/package context.
- **what:** standardize docs/scripts on explicit discovery command (`python3 -m unittest discover -s tests -p "test_*.py"`).
- **acceptance:** QA docs and validation scripts use deterministic test-discovery invocation.

## Execution order
1. `R6` and `R5` (truth + liveness)
2. `R7` and `R9` (observability + parser robustness)
3. `R8` and `R10` (hygiene)
4. `R3` then `R4` (neutrality completion + wrapper retirement)
5. `R1` and `R2` maintained as portability references

## D — Deep remediation documentation (post 2026-05 incident analysis)

Operational narrative: dual-track run (direct factory vs relay bridge), stale `queue/worker.lease`, `mvr` seed-only evidence, `delivery_status: not_queued`.

| id | artifact | status |
|----|-----------|--------|
| `deep-doc-analysis` | `docs/qa/RFO-DEEP-ANALYSIS-2026-05.md` | completed |
| `deep-doc-roadmap` | `docs/qa/RFO-REMEDIATION-ROADMAP.md` | completed |
| `deep-doc-lease-runbook` | `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` | completed |
| `deep-doc-truth-map` | `docs/qa/RFO-TRUTH-CONTRACTS-ALIGNMENT.md` | completed |
| `deep-doc-matrix-rows` | `docs/qa/assertion-command-matrix.md` updated (deep remediation rows) | completed |

Follow-up coding items that remain intentionally open are listed **by workstream** in `RFO-REMEDIATION-ROADMAP.md` (workstreams A–E forward phases).

## E — Deep remediation execution phases (forward work)

Ordered program for closing **Critical/High** items from [RFO-DEEP-ANALYSIS-2026-05.md](./RFO-DEEP-ANALYSIS-2026-05.md). Status here is **planning tracker**; detailed acceptance lives in the roadmap.

| Phase | Focus | Primary artifacts / code | Exit criteria (summary) |
|-------|--------|--------------------------|-------------------------|
| **E1** | Queue/lease liveness + operator ergonomics | `worker_impl.py`, `RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` | No starvation from poison jobs; lease triage ≤5 min; stderr/runbook pointers where applicable |
| **E2** | Truth boundary (compute vs delivery) + outbox coherence | `artifact_execute_impl.py`, `outbox_impl.py`, `validate_gate_semantics.py` | Gates and manifests cannot be misread as “delivered” when only compute ran |
| **E3** | Profile / validation parity (epistemic harm) | profiles, `verify_skill_run_claims.py`, playbook | Hard tasks do not silently present stub/seed as full external research |
| **E4** | Anti-regression & contracts | `RFO-TRUTH-CONTRACTS-ALIGNMENT.md`, `assertion-command-matrix.md`, schemas | Schema/contract changes paired with validator + matrix updates |
| **E5** | Operational guardrails hardened | bridge sanity gate, `errors.jsonl` volume review | Best-effort and relay paths fail closed; observability budget acceptable |

**Cross-links:** [RFO-REMEDIATION-ROADMAP.md](./RFO-REMEDIATION-ROADMAP.md) (workstreams A–E), [NEUTRALITY-SCAN.md](./NEUTRALITY-SCAN.md) (canonical doc bundle table).

## Done definition
- All items above are merged in this repository.
- If code is later ported elsewhere, this file records the target commit/hash copied out.
