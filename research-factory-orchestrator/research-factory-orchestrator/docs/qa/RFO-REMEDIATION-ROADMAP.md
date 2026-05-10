# RFO remediation roadmap — deep failure closure

**Status:** living document  
**Companion:** [RFO-DEEP-ANALYSIS-2026-05](./RFO-DEEP-ANALYSIS-2026-05.md)

This roadmap matches the **Deep Failure Analysis** workstreams: each has **owner-intent** (what we optimize for), **primary risk**, **rollback strategy**, and **acceptance criteria**. Items marked **DONE (local)** are already merged in this repository.

---

## Workstream A — Queue / lease reliability

**Owner-intent:** One predictable worker claim per healthy `runs-root` **without** manual `rm worker.lease` in steady state.

**Primary risk:** Liveness (bridge / automation starves while lease or poison job blocks).

**Rollback strategy:** Revert `runtime/worker_impl.py` parking/backoff + token change **only** if production shows pathological starvation from backoff math; restore prior “first pending only” semantics is a last resort and loses FM-POISON mitigation.

| Phase | Deliverable | Acceptance |
|-------|-------------|------------|
| 1 — DONE (local) | Poison-job backoff / parking | `queue/failure-meta.json` records attempts + `parked_until_ts`; other jobs can be claimed |
| 2 — DONE (local) | Lease token matches **selected** pending job | `sid(..., selected_pending.name, ...)` in `cmd_worker` |
| 3 | Documented single-writer contract for `queue/` | ADR/note: one active worker process per `runs-root` **or** documented multi-host unsupported |
| 4 — forward | Optional lease heartbeat during long subprocess | Long jobs do not extend “stale” confusion beyond TTL semantics |
| 5 — forward | Stronger lock (OS / flock) | Only if multi-process on **one** host is required |

---

## Workstream B — Truth / gate semantics

**Owner-intent:** No artifact implies **outbound delivery proof** when only **compute** ran.

**Primary risk:** **Overconfidence** — readers treat `final-answer-gate.passed` or HTML polish as “shipped to user” or “externally validated”.

**Rollback strategy:** Revert narrower `final-answer-gate` writes only with coordinated schema + validator updates; prefer additive fields (`compute_phase`, `delivery_deferred`) over removing `passed`.

| Phase | Deliverable | Acceptance |
|-------|-------------|------------|
| 1 | Cross-link ADR-016 in playbooks | Every operator path states compute vs gateway delivery |
| 2 — forward | Explicit `artifact_execute` gate labeling | Discriminate **content_ready** vs **delivery_proven** without breaking `validate_gate_semantics.py` |
| 3 | Honesty chain | `verify_skill_run_claims.py` catches grand claims under `seed_only` / `delivery_not_proven` |

**Code anchors:** `runtime/artifact_execute_impl.py` (execute path gate), `runtime/outbox_impl.py` (ACK-driven `delivery_not_proven`), `scripts/verify_skill_run_claims.py`.

---

## Workstream C — Profile / validation parity

**Owner-intent:** Analytical difficulty maps to **evidence policy** without silent downgrade to stub-only.

**Primary risk:** User-trust loss — beautiful report + zero real sources.

**Rollback strategy:** Feature flags / env-only escalation; disable heuristic if false positives block CI.

| Phase | Deliverable | Acceptance |
|-------|-------------|------------|
| 1 | Playbook preflight: default relay profile | [`RFO-FULL-RESEARCH-PLAYBOOK.md`](./RFO-FULL-RESEARCH-PLAYBOOK.md) warns when `mvr` + relay |
| 2 — forward | Escalation hook (`RFO_MIN_SOURCES`, task classifier stub, etc.) | Hard tasks refuse `mvr` or auto-switch to `live-bridge` |
| 3 — forward | HTML banner when `stub_only_allowed` | Visible “evidence-lite mode” |

---

## Workstream D — Delivery / outbox correctness

**Owner-intent:** Outbox updates **delivery-manifest**, **final-answer-gate**, **runtime-status** coherently after ACKs; no silent swallow of packaging errors.

**Primary risk:** Operator cannot tell **why** delivery failed — swallowed exceptions (reduced by structured `runtime/errors.jsonl`).

**Rollback strategy:** Revert outbox logging changes if log volume breaks disk quotas; keep **narrow** exception scopes.

| Phase | Deliverable | Acceptance |
|-------|-------------|------------|
| 1 — DONE (local) | Package rebuild failures logged | `outbox_package_rebuild_failed` in `runtime/errors.jsonl` where applicable |
| 2 | `delivery_not_proven` surfaces reasons | `outbox_impl.py` aligns with `validate_delivery_manifest_requires_ack.py` expectations |
| 3 | Contract sync | [`RFO-TRUTH-CONTRACTS-ALIGNMENT.md`](./RFO-TRUTH-CONTRACTS-ALIGNMENT.md) updated when gate shapes change |

---

## Workstream E — Operational guardrails

**Owner-intent:** Failures are **actionable** (stderr points to runbook, path guard errors are clear).

**Primary risk:** Long MTTR on lease incidents; false confidence from best-effort bridge.

**Rollback strategy:** Remove stderr hints if log parsers break; keep sanity gate ON for `--best-effort-continue`.

| Phase | Deliverable | Acceptance |
|-------|-------------|------------|
| 1 — DONE (local) | Bridge stdout JSON + best-effort gate | Multiline JSON; incomplete runs exit non-zero |
| 2 — forward | Stderr tail on `lease_present` | References `RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` |
| 3 | Path guard docs | `/tmp` + `RFO_ALLOW_TMP_RUNS_ROOT` documented in playbook |

---

## Cross-workstream execution order

1. **A** (liveness) + **E** (ergonomics) — unblock operators.  
2. **B** + **D** (truth + outbox) — align gates and manifests.  
3. **C** (profile) — reduce epistemic harm on production tasks.  

---

## Program-level done definition

- No **P0** lease incident without a documented recovery path (runbook).  
- No **silent** best-effort handoff on incomplete worker artifacts.  
- **Critical/High** items in [RFO-DEEP-ANALYSIS-2026-05 §4](./RFO-DEEP-ANALYSIS-2026-05.md#4-critical-findings-severity--code-anchors) each have a repro row (§5), acceptance in a workstream above, and rollback noted here.

---

## Legacy section — internal WS1–WS5 labels (mapping)

For historical chat references: **WS1** ≈ A, **WS2** ≈ C, **WS3** ≈ E + B UX, **WS4** ≈ E bridge, **WS5** ≈ B + D docs/tests.
