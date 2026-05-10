# RFO deep analysis — incident bundle (2026-05)

**Classification:** post-incident technical analysis + root-cause map  
**Source log:** operator “RFO Analysis Log: Мировые запасы нефти” (2026-05-10)  
**Skill line:** v19.3.x (see `runtime/version.json`)

This document is **evidence-driven**: it ties observed symptoms to mechanisms in this repository and states what is **by design**, what is **misconfiguration**, and what remains **hazardous** after recent mitigations.

---

## 1. Executive summary

Two parallel execution paths were used for the same analytical task:

| Track | Entry | Outcome (as reported) |
|-------|--------|------------------------|
| A | `scripts/run_research_factory.py` | `content_rendered`, HTML + chat memos present |
| B | `scripts/run_rfo_with_web_search.py` | Worker never claimed job after 12 retries |

The user-facing failure combined **(i)** a **queue lease** blocking the worker, **(ii)** **profile `mvr`** producing **seed-only** evidence (no external URLs), and **(iii)** **delivery** remaining `not_queued` because the **outbox / host delivery** contour was not exercised — which is consistent with **artifact-only compute** (ADR-016) but easy to misread as “broken delivery”.

---

## 2. Incident timeline (state divergence by track)

| Time (UTC) / phase | Track A (`run_research_factory`) | Track B (`run_rfo_with_web_search` + queue) |
|--------------------|----------------------------------|---------------------------------------------|
| Start | Creates/uses `run_dir`, runs runtime inline path | Prefetch + enqueue + **worker claim** required |
| Collection | `mvr`: `EXTERNAL-COLLECTION-NO-SEEDS` if no seeds | Same profile semantics if same env |
| Render | `content_rendered`, HTML ~433 lines, `chat/*.md` | Blocked upstream if worker never claims |
| Queue | May bypass `queue/pending` altogether | Job in `queue/pending`; lease may block `claimed: true` |
| Delivery manifest | `not_queued` if no outbox worker | Same; bridge retries show `lease_present` |

**Run IDs (from log):** `RUN-6ae0427cb03f` (factory path success) vs `RUN-11c13028274d` (bridge path stuck). **Do not merge** “done” semantics across tracks without matching `run_id`.

---

## 3. Fault taxonomy

| Class | Definition | Examples from this incident |
|-------|------------|----------------------------|
| **Policy mismatch** | Runtime behaved per profile/contracts; operator expected richer evidence or delivery | `mvr` + heavy question → stub sources; `not_queued` without host outbox |
| **Code / design hazard** | Implementation allows liveness or truth edges that bite under load | Lease file + mtime TTL; non-atomic cross-host claim |
| **Ops / environment** | Stale lease, wrong `RUNS_ROOT`, missing relay URL, duplicate workers | Orphan `worker.lease`; `/tmp` guard without allow flag |
| **Misread artifacts** | Human reads `passed` / “report ready” as “sent” or “proven” | ADR-016 boundary not internalized |

---

## 4. Critical findings (severity + code anchors)

| ID | Severity | Finding | Code / artifact anchors |
|----|----------|---------|---------------------------|
| CF-1 | **Critical** | Worker refuses claim while `queue/worker.lease` exists and is **fresh** (`age < TTL`), even if PID is dead — up to **15 min** default | `runtime/worker_impl.py`: `_unlink_stale_lease`, `cmd_worker` (~L529–L547) |
| CF-2 | **High** | Same lease file is **not** a distributed lock; two hosts sharing one `runs-root` → undefined behaviour | `worker_impl.py` (design); ops contract |
| CF-3 | **High** (mitigated) | `--best-effort-continue` could hand off degraded runs | `scripts/run_rfo_with_web_search.py`: `_bridge_best_effort_sanity_gate` |
| CF-4 | **High** | **`mvr`** allows seed-only output for tasks that need external evidence — **policy-correct, outcome-wrong** | `contracts/run-profiles.json` / profile pipeline |
| CF-5 | **Medium** | `artifact_execute` writes `final-answer-gate.json` with **`passed: true`** on success path; semantics are **compute completion**, not outbound delivery proof | `runtime/artifact_execute_impl.py` (~L388–L397); contrast `runtime/outbox_impl.py` ACK-driven gates |
| CF-6 | **Medium** | `feature-truth-matrix` keys vs validator coverage can drift; “scaffold” reads as “broken” | `feature-truth-matrix.json`; `scripts/validate_skill.py` required_scripts |
| CF-7 | **Low** | Lease token forensic alignment (fixed): token must match **selected** job file | `runtime/worker_impl.py` — uses `selected_pending.name` |

---

## 5. Repro matrix

| Scenario | Minimal repro | Expected honest signal | Pass / fail check |
|----------|---------------|------------------------|-------------------|
| **Lease block** | Create `queue/worker.lease`, age &lt; TTL; run worker | `{"claimed": false, "reason": "lease_present"}` | Clear lease after confirming dead PID (see runbook) |
| **Stale lease** | Touch lease with old mtime OR wait TTL; run worker | Stale lease removed, claim proceeds | `RFO_WORKER_LEASE_STALE_SECONDS` |
| **Poison job head** | Pending job always timeout/exit ≠0 | Other pendings eventually claimed after **park** expires | `queue/failure-meta.json` |
| **mvr seed-only** | `run_rfo_with_web_search.py --profile mvr` without seeds | `EXTERNAL-COLLECTION-NO-SEEDS`; stub sources | Switch profile or set `RFO_WEB_SEARCH_JSON_API_BASE` |
| **Best-effort handoff** | Worker fail + `--best-effort-continue` + incomplete artifacts | Exit **1**, no handoff | Sanity gate |
| **Gate vs delivery** | Compare `artifact_execute` run vs `outbox` run | Execute: compute `passed`; outbox: may `delivery_not_proven` | Read both `final-answer-gate.json` + `delivery-manifest.json` |

**Proposed fixes, acceptance tests, rollback** for CF-1–CF-5 are consolidated in [`RFO-REMEDIATION-ROADMAP.md`](./RFO-REMEDIATION-ROADMAP.md) (per workstream).

---

## 6. Blast radius

| Failure | Distorted artifact / gate | User-visible risk |
|---------|---------------------------|-------------------|
| Lease stuck | Job never reaches `delivery_queued`; bridge spins | “Nothing happens” / retries exhaust |
| `mvr` on hard task | Rich HTML, **weak** `sources.json` | Looks authoritative; citations absent |
| `not_queued` + no host | Honest manifest | User thinks “bot broken” |
| Misread `final-answer-gate.passed` after execute | `passed: true` in artifact-only path | Claims “complete” without delivery proof |
| Truth matrix **stub** | Banner says scaffold | Trust collapse if labeled as full rigor |

---

## 7. Observed symptoms (normalized)

1. **Bridge / worker:** `claimed: false`, reason `lease_present` or “no pending jobs” after retries; `queue/worker.lease` appears **stale** from the operator’s perspective.
2. **Collection:** `runtime/errors.jsonl` records `EXTERNAL-COLLECTION-NO-SEEDS` with `profile: mvr`, `external_mode: off`.
3. **Sources:** `sources.json` effectively **stub-only** (`stub:seed-only`), `citation_eligible: false`.
4. **Delivery manifest:** `delivery_status: not_queued`, no attachments, `real_external_delivery: false`.
5. **Feature truth:** multiple capabilities marked `missing`, `stub`, or `implemented_scaffold` — accurate for a minimal / non-networked contour.
6. **Path policy (reported confusion):** operator believed `run_rfo_with_web_search.py` rejected a **valid** workspace path as `/tmp`; the guard only blocks `--runs-root` **inside** `/tmp` without `RFO_ALLOW_TMP_RUNS_ROOT=1` (intentional safety policy, not path corruption).

---

## 8. Root-cause analysis

### RC-A — Single-flight lease + TTL semantics (`queue/worker.lease`)

**Mechanism:** `runtime/worker_impl.py` implements a **process-wide lease file** under `<runs-root>/queue/worker.lease`. If the file exists and is **newer** than `RFO_WORKER_LEASE_STALE_SECONDS` (default **900s**), the worker returns `{"claimed": false, "reason": "lease_present"}`.

**Why it hurts:** Any crash, kill, or stuck process that **leaves the lease without unlinking** can block claims for up to the TTL. The bridge’s retry loop then looks like “job stuck in pending forever”.

**Mitigated in-repo:**

- Bounded **park/backoff** for poison jobs via `queue/failure-meta.json` (`_select_pending_job_with_backoff`, `_record_worker_failure`).
- Lease token aligns with **selected** pending job name (forensics).

**Residual risk:** Lease is **not** an atomic multi-host lock; two workers on different hosts sharing one `runs-root` can still race.

### RC-B — Profile `mvr` vs analytical task complexity

**Mechanism:** `mvr` sets `web_search_required: false`, allows stub-only sources, and does not require external collection. **Intentional** for minimal smoke paths.

**User impact:** A “serious” question still produces **structurally complete** run (HTML, memos) with **near-zero independent evidence**.

**Classification:** **expectation mismatch**. Fix: routing policy or auto-escalation (roadmap).

### RC-C — `EXTERNAL-COLLECTION-NO-SEEDS`

With `RFO_SEED_URLS` empty and external collection off, collector records a **warning**. Under `mvr` this is **consistent**.

### RC-D — `delivery_status: not_queued`

**Boundary truth (ADR-016).** Do not equate `content_rendered` with “user received file”.

### RC-E — Parallel tracks and queue truth

Direct factory may complete **without** the same enqueue path as the relay bridge — contradictory queue states refer to **different** `run_id`s.

---

## 9. Failure mode IDs (for runbooks / tests)

| ID | Mode | Detection | Safe response |
|----|------|-----------|---------------|
| FM-LEASE-BLOCK | Stale or orphan `worker.lease` | `reason: lease_present`, age < TTL | [Lease runbook](./RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md) |
| FM-POISON-JOB | Repeated worker timeout/returncode | `queue/failure-meta.json` | Wait for backoff or inspect job payload |
| FM-PROFILE-UNDERKILL | `mvr` on evidence-heavy task | feature matrix + `EXTERNAL-COLLECTION-NO-SEEDS` | Change profile / add relay |
| FM-DELIVERY-ABSENT | `not_queued` | `delivery-manifest.json` | Outbox/host delivery or accept compute-only |
| FM-PATH-GUARD | `/tmp` runs root blocked | stderr from bridge | Persistent `RUNS_ROOT` or allow env |

---

## 10. Mapping: log fields → repository artifacts

| Log mention | Typical path under `run_dir` or `runs-root` |
|-------------|---------------------------------------------|
| Worker lease | `<runs-root>/queue/worker.lease` |
| Pending job | `<runs-root>/queue/pending/JOB-*.json` |
| Runtime state | `<run_dir>/runtime-status.json` |
| Collection warning | `<run_dir>/runtime/errors.jsonl` |
| Capabilities | `<run_dir>/feature-truth-matrix.json` |
| Delivery | `<run_dir>/delivery-manifest.json` |
| Honesty checks | `scripts/verify_skill_run_claims.py --run-dir …` |

---

## 11. Conclusion

The incident is **three overlapping stories**: **liveness** (lease + queue), **epistemic** (`mvr` vs task), **product boundary** (compute vs host delivery).

Further work: [`RFO-REMEDIATION-ROADMAP.md`](./RFO-REMEDIATION-ROADMAP.md), [`RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`](./RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md).

---

## 12. References

- [ADR-016 — compute vs delivery split](../adr/ADR-016-compute-vs-delivery-split.md)
- [ADR-018 — bridge handoff and portable paths](../adr/ADR-018-bridge-handoff-and-portable-paths.md)
- [RFO-FULL-RESEARCH-PLAYBOOK](./RFO-FULL-RESEARCH-PLAYBOOK.md)
- [RFO-TRUTH-CONTRACTS-ALIGNMENT](./RFO-TRUTH-CONTRACTS-ALIGNMENT.md)
