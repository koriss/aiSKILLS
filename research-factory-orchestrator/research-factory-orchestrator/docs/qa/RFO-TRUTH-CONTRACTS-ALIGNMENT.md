# RFO truth contracts alignment

Maps **runtime writers** → **contracts / schemas** → **validators** → **report & chat surfaces**. Use when auditing “pass vs delivered vs evidence-backed” regressions.

Related: ADR **001**, **016**, **018** — [`ADR-016`](../adr/ADR-016-compute-vs-delivery-split.md) is the authoritative compute/delivery boundary.

---

## 1. End-to-end alignment map (normative)

| Stage | Primary writer(s) | Key artifacts | Schemas / contracts | Validators / scripts (representative) |
|-------|-------------------|-----------------|---------------------|----------------------------------------|
| Execute / CLI compute | `runtime/artifact_execute_impl.py`, `scripts/rfo_runtime_core.py` | `final-answer.md`, `result-manifest.json`, `final-answer-gate.json`, `marker.json` | `contracts/result-manifest-contract.json`, `schemas/core/delivery-manifest.schema.json` (cross refs), `package-required-artifacts.json` | `validate_artifact_release.py`, `verify_skill_run_claims.py` |
| Queue worker + package | `runtime/worker_impl.py` | `outbox/*.json`, `runtime-status.json` → `delivery_queued` | `contracts/outbox-contract.json`, `canonical-package-layout-contract.json` | `validate_outbox_delivery.py`, `validate_job_lifecycle.py` |
| Outbox / delivery | `runtime/outbox_impl.py` | `delivery-manifest.json`, `final-answer-gate.json`, `attachment-ledger.json`, `runtime-status.json` | `schemas/core/delivery-manifest.schema.json`, `drafts/schemas/core/final-answer-gate.schema.json` | `validate_delivery_manifest_requires_ack.py`, `validate_gate_semantics.py`, `validate_logical_consistency.py` |
| HTML / chat surface | `runtime/report_html.py`, `runtime/chat_md.py` | `report/full-report.html`, `chat/*.md` | Embedded JSON IDs per `validators-core` | `tests.test_report_html_citations`, manual capability blocks |

---

## 2. State machine (`runtime-status.json`)

| State | Typical meaning | Who advances |
|-------|-----------------|--------------|
| early → `content_rendered` | HTML + chat present | runtime |
| `delivery_queued` | Outbox written; package built | `worker_impl.cmd_worker` after subprocess success |
| Host-specific “delivered” | Not asserted by compute-only skill | gateway / adapter |

**Truth:** `content_rendered` **does not** imply user-visible delivery (ADR-016).

---

## 3. `final-answer-gate.json` — two legitimate semantics

| Origin | Typical `passed` / `status` | Meaning |
|--------|------------------------------|---------|
| **`artifact_execute_impl`** | `passed: true`, `status: pass` on successful pipeline | **Content / package readiness** for handoff; **not** proof of external send |
| **`outbox_impl`** (post-ACK) | Derived from ACKs + `delivery_not_proven` | **Delivery truth** — may be `delivery_not_proven`, `stub_delivered`, etc. |

**Drift risk:** Readers who only open the gate file after **execute** may over-read “passed” as “delivered”. Mitigation: always pair with `delivery-manifest.json` and profile.

**Code:** `runtime/artifact_execute_impl.py` (~388–397); `runtime/outbox_impl.py` (manifest + gate rewrite ~334–380).

---

## 4. Delivery manifest

| Field | Semantics | Common pitfall |
|-------|-----------|----------------|
| `delivery_status` | Pipeline state | `not_queued` = compute-only or worker not run |
| `real_external_delivery` | Outbound proof | `false` valid for CLI |
| `stub_delivery` | Synthetic path | must not be sold as live send |

Schema: `schemas/core/delivery-manifest.schema.json`.

---

## 5. Feature truth matrix (`feature-truth-matrix.json`)

| Class | Meaning |
|-------|---------|
| `implemented` | Functional in contour |
| `implemented_scaffold` | Structure only |
| `stub` | Explicit non-production |
| `missing` | Not wired |

**Drift pairs (watchlist):**

| Observed | Resolution |
|----------|------------|
| Docs promise key `external_user_visible_delivery_via_skill` but matrix omits | Update writer in runtime OR doc (prefer code+matrix sync) |
| Validators reference legacy `gates` vs `checks` | Standardize on `checks` per `operating-discipline.md` / outbox rewrite |
| `delivery_not_proven` in ACK but gate still `passed` | Inspect `outbox_impl` merge rules — may be intentional “content ready” vs strict lifecycle validators |

---

## 6. Bridge handoff (`__RFO_SKILL_AGENT_HANDOFF__=`)

| Concern | Mitigation |
|---------|------------|
| Marker not on last line | ADR-019, `parse_handoff_stdout_reference.py` |
| JSON in logs | `_parse_stdout_json_object` incremental scan |
| Best-effort false success | `_bridge_best_effort_sanity_gate` in `run_rfo_with_web_search.py` |

---

## 7. Validator script index (quick ref)

| Concern | Script |
|---------|--------|
| Claim vs artifacts | `scripts/verify_skill_run_claims.py` |
| Gate vs manifest consistency | `scripts/validate_gate_semantics.py`, `scripts/validate_logical_consistency.py` |
| Stub vs real delivery | `scripts/validate_stub_delivery_not_external.py` |
| Outbox finalization | `scripts/validate_outbox_finalization.py` |
| Skill tree | `scripts/validate_skill.py` |

---

## 8. Change process

When editing **states**, **gate shapes**, or **manifest fields**:

1. Update **this file** and [`assertion-command-matrix.md`](./assertion-command-matrix.md).  
2. Bump or cite **`schemas/core/*.schema.json`** as needed.  
3. Adjust **`contracts/*`** if boundary contracts change.  
4. Add failure-corpus fixture if regression is safety-critical.

---

## 9. Known gaps (forward work)

See [RFO-REMEDIATION-ROADMAP.md](./RFO-REMEDIATION-ROADMAP.md) workstreams **B** (gate semantics) and **C** (profile parity).
