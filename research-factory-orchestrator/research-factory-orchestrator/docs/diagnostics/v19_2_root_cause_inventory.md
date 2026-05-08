# RFO v19.2.0 — Root-cause inventory (Phase 1 cross-cut investigations)

**Branch:** `feat/v19-2-0-runtime-truth`
**Base:** `main` @ `4987736` (v19.1.0)
**Generated:** Phase 1 of `rfo-v19.2-runtime-truth_18ae4d27.plan.md`

This is **not** a re-audit of the ChatGPT "truth-integration hardened" archive (which lives outside this repo). It is the inventory of what the v19.1.0 codebase actually contains, mapped against the failure modes the operator and the static audit reported. Every row points to the Phase that owns the fix.

---

## H1 — Layout audit (run-dir vs runs-root)

**Status:** consistent. Both `runs_root/runs/<run_label>/...` and direct `--project-dir <run_dir>` are supported.

- `runtime/cli.py` — `run --project-dir`, `worker --runs-root`, `outbox --runs-root` are the three layouts in active use.
- `runtime/worker_impl.py:cmd_worker` reads `root / "queue/pending"`, writes `queue/running`, `queue/done`, `queue/worker.lease` — runs-root layout.
- `runtime/worker_impl.py:cmd_run` writes everything inside `rd = Path(a.project_dir)` — run-dir layout.
- `runtime/outbox_impl.py` walks `runs/<label>/...` discovered from `runs_root`.

**Risk:** dual layout is fine, but artifacts produced under `runs_root/runs/<label>/...` need root-vs-zip parity check (Phase 4B `validate_root_vs_zip_artifact_truth`).

**Phase:** none (verified). Reuse evidence in Phase 5 smoke `_smoke_root_vs_zip_artifact_truth`.

---

## H2 — Field diff (v18 vs v19) in active runtime

| File | Line | Symbol | Issue | Phase |
|---|---|---|---|---|
| `runtime/worker_impl.py` | 114 | `"gates": {}` in delivery-manifest overrides | v18 field name; v19 uses `checks` | Phase 2 (T2.x) |
| `runtime/worker_impl.py` | 130 | `event_name: "v18.runtime.started"` | hardcoded v18 string in events | Phase 2 (T2.x) |
| `runtime/worker_impl.py` | 179 | `event_name: "v18.runtime.completed"` | hardcoded v18 string in events | Phase 2 (T2.x) |
| `runtime/outbox_impl.py` | 182–183 | `cr.get("relevance_aware_factuality_score", 0.85)` / `cr.get("deflection_rate_when_no_grounding", 0.5)` | magic optimistic defaults from claims-registry | Phase 4C (T4C.6) + Phase 4B (`validate_citation_grounding`) |
| `runtime/outbox_impl.py` | 184 | `citation_grounding_gate_pass = raf >= 0.7 and dfl >= 0.3` | citation grounding decided in outbox by magic defaults instead of validator | Phase 4B (`validate_citation_grounding` → outbox reads validator verdict) |
| `runtime/outbox_impl.py` | 222, 243 | `"gates": gates` written into `delivery-manifest.json` and `final-answer-gate.json` | v18 key in v19 active artifacts | Phase 2 (T2.2) |
| `runtime/outbox_impl.py` | 244–245 | RAF/DFL float fields written into `final-answer-gate.json` | v18 field names persisted | Phase 4C (T4C.6) |
| `runtime/render.py` | 122–123 | `"relevance_aware_factuality_score": 0.85`, `"deflection_rate_when_no_grounding": 0.55` | hardcoded magic in claims-registry | Phase 4C (T4C.6) |
| `runtime/render.py` | 333 | HTML title `"Research Factory Orchestrator v18 — Internal Analysis/Audit Report"` | v18 string in user-visible HTML | Phase 2 (T2.x) |
| `runtime/validate_impl.py` | 151 | `gates = fg.get("gates", {})` | reads only v18 key, breaks against v19 emitter | Phase 4C (T4C.5) → move to `legacy_compat.py` |
| `runtime/failure_impl.py` | 89 | `"missing v18.7 bad run_dir"` | v18 string in skipped reason | Phase 9 (versions/docs sweep) |
| `runtime/operating-discipline.md` | 16 | `"v18.7"` in invariant text | v18 reference in active discipline | Phase 9 |

**Cross-check vs static audit P1-1..P1-10:** every audit row points to a file that exists in the hardened archive but not yet in this repo (`runtime/external_collect.py`, `runtime/work_units.py`, `runtime/v19_core_artifacts.py`, `runtime/truth_integration.py`). Those are **net-new** modules built in Phase 4 / 4B / 4C. The repo-side v18 fields above are independent and must be killed in Phase 2 + 4C even before the new modules land.

---

## H3 — Hardcoded v18 strings (literal `v18.`, `LIGHTWEIGHT_RESEARCH`)

| Token | File | Line | Verdict | Phase |
|---|---|---|---|---|
| `LIGHTWEIGHT_RESEARCH` | `examples/example-simple-research.md` | 5 | violates `validate_code_hygiene` | Phase 4C (T4C.8) |
| `LIGHTWEIGHT_RESEARCH` | `tests/quality-gates/no-lightweight-mode.md` | 3 | guideline against it (allowed) | keep |
| `LIGHTWEIGHT_RESEARCH` | `scripts/validate_code_hygiene.py` | 4 | enforcement allowlist target (allowed) | keep |
| `v18.runtime.started` / `v18.runtime.completed` | `runtime/worker_impl.py` | 130, 179 | event name literals | Phase 2 |
| `RFO v18 ... Internal Analysis/Audit Report` | `runtime/render.py` | 333 | user-visible HTML title | Phase 2 |
| `missing v18.7 bad run_dir` | `runtime/failure_impl.py` | 89 | skipped-reason string | Phase 9 |

**Note:** `LIGHTWEIGHT_RESEARCH` does **not** appear in `SKILL.md`. The leak is isolated to `examples/example-simple-research.md`.

---

## H4 — Rollback bypass scan

`validation_failed` and `rollback` references found in 11 files. Active production paths:

- `runtime/schema_defaults.py:21,152` — `delivery_status: "validation_failed"` is the canonical fallback for V1 failure (correct, fail-closed).
- `runtime/smoke_impl.py:25` — guards smoke against `validation_failed`.
- `runtime/validate_impl.py` — emits `validation_failed` on V1 fail.
- `scripts/validate_no_delivery_after_validation_fail.py` — already enforces "no delivery after validation_failed".
- `scripts/validate_logical_consistency.py` — LC01 accepts both `failed` and `validation_failed` (added in v19.1.0).
- `scripts/_smoke_rollback_creates_stubs.py` — proves rollback semantics.

**Observation:** No active code path lets `production_ready: true` co-exist with `validation_status: failed`. `production_ready` is **not** referenced anywhere in this repo (zero matches). The user-reported "validation failed but production_ready: true" came from an **upstream news-catalog** pipeline that lives outside this repo. **Phase 6 task** still adds `validate_no_failed_validation_in_production` as a guard so the same class of bug cannot regress here.

**Phase:** Phase 6 (T6.x — `validate_no_failed_validation_in_production`).

---

## H5 — Claim-status / delivery-status legacy

Vocabulary in active `runtime/outbox_impl.py:200–211`:

- `dstat ∈ {"failed", "delivered", "stub_delivered", "partial_delivery"}`
- `fg_status ∈ {"fail", "pass", "stub_only"}`

Plus `runtime/schema_defaults.py` adds `"validation_failed"` for V1 rollback. All five values are documented in `contracts/state-machine.json` and `runtime/compatibility-matrix.json`. **No drift detected.**

`stub_delivered` and `stub_only` are **honest semantics**, not bugs. They are exactly what Phase 4B requires for `mvr/no-backend` (honest stub). The bug is upstream: when collection has no sources, the WU lifecycle currently completes silently as "done" instead of being labelled `completed_no_sources` / `blocked_missing_backend` (Phase 4C T4C.4).

---

## H6 — Duplicate / orphan entrypoints

| Entrypoint | Role | Action |
|---|---|---|
| `scripts/rfo_v18_core.py` | thin facade `from runtime.cli import main` | rename to `rfo_runtime_core.py` (Phase 6 T6.2) + leave deprecated shim |
| `scripts/runtime_job_worker.py` | shim that `runpy.run_path(rfo_v18_core)` with `argv=["...", "worker", ...]` | retarget to `rfo_runtime_core.py` (Phase 6 T6.2) |
| `scripts/run_research_factory.py` | research orchestrator | inspect for v18 references in Phase 6 |
| 17 dependents of `rfo_v18_core` (`scripts/*` + `runtime/{smoke,worker}_impl.py`) | string references | sweep in Phase 6 T6.2 |

**Critical:** `runtime_job_worker.py` does not execute work units. It just runs **one** `pending[0]` job through `cmd_run` (which itself only renders). The 12 work units written to `work-queue/pending/WU-XXX.json` are never claimed, never executed. This is the root cause of `feature-truth-matrix["analytical_memo"] = "scaffold"`, `["wave_graph_collector"] = "scaffold"`, etc.

**Phase:** Phase 3 (T3.x — `cmd_worker` loop over `work-queue/pending/`, per-WU evidence, ledger transitions, `work_unit_started`/`work_unit_completed` events, `validate_work_unit_completion` guard). The static-audit P1-13 (`collection_completed increments even for completed_no_external_results`) is the Phase 4C T4C.4 negative requirement on top of Phase 3.

---

## H7 — Vocabulary (seed_only / external_collection_executed / scaffold)

`seed_only` appears in:

- `runtime/render.py:96` — `"strength": "seed_only"` on a confidence cluster (semantically correct: this is a default cluster strength, not a runtime flag).
- `scripts/validate_seed_claims_not_presented_as_domain_analysis.py` — guard.
- `scripts/validate_smoke_run_not_presented_as_research.py` — guard.
- `contracts/smoke-run-contract.json` — contract reference.

`external_collection_executed` does **not** appear anywhere in this repo. It exists only in the hardened archive (the audit refers to `runtime/external_collect.py:144`). Phase 4 + 4C T4C.2 will introduce it as **split flags** instead of one bool: `web_search_attempted`, `web_search_result_count`, `web_search_succeeded`, `source_packet_loaded`, `external_sources_loaded`. No legacy bool to preserve.

`feature-truth-matrix.json` is hardcoded in `runtime/worker_impl.py:131–151`:

```text
"wave_graph_collector": "scaffold",
"real_external_search_workers": "missing",
"provider_telegram_real_send": "stub",
"analytical_memo": "scaffold",
"factual_dossier": "scaffold",
"io_propaganda_check": "scaffold",
"self_audit": "scaffold",
```

Phases 3 + 4 + 7 must update each value to `implemented` only when the corresponding subsystem actually runs. Phase 6 T6.1 (`validate_no_scaffolds_in_production`) blocks `production` mode runs from emitting any `scaffold`/`stub`/`missing`.

---

## H8 — Providers

`runtime/outbox_impl.py` orchestrates per-provider gates. There is **no real Telegram send adapter** in `runtime/` — `provider_telegram_real_send` is `"stub"` in the feature matrix because the actual adapter is in `tools/agent_telegram/` from the v19.0.5 fork (Phase 7 port). Until Phase 7 lands, `mvr` profile keeps `delivery_mode: stub_allowed_explicit` (already correct in `validation-profiles/mvr.json:25`); `full-rigor` keeps `real_external_only_unless_explicit_stub` (already correct in `validation-profiles/full-rigor.json:25`).

---

## H9 — Production-claim hygiene

- `production_ready` field — **0 matches** in this repo. Safe.
- `validation_status` — emitted as `pending_dag` then resolved by the validator DAG. No co-existence with `production_ready`.
- `delivery_status: "stub_delivered"` is currently treated as `delivery_ok = 1.0` in `runtime/slo.py:22` (`delivery_ok = 1.0 if str(dm.get("delivery_status") or "") in ("delivered", "stub_delivered") else 0.0`). **This is the SLO leak**: an honest stub run still counts as a successful delivery for SLO purposes. Phase 6 T6.x — split SLO so that `stub_delivered` does not satisfy `delivery_ok` for production-mode runs.

**New Phase 6 follow-up:** add `validate_slo_stub_delivery_not_production_ok` (extending T6.x).

---

## H10 — Static-audit P0/P1/P2 (already encoded in plan)

The static audit findings cover modules **not yet present** in this repo (`runtime/external_collect.py`, `runtime/work_units.py`, `runtime/v19_core_artifacts.py`, `runtime/truth_integration.py`, `runtime/legacy_compat.py`, `validation-profiles/{mvr,full-rigor,book-verification,propaganda-io}.json` validator alignment). Mapping is already in plan section "Static-audit P0/P1 (ChatGPT, 2026-05-06)" and Phase 4C tasks T4C.1 — T4C.9. No additional phases needed — the audit becomes the **negative requirement contract** for Phase 4 / 4B / 4C net-new code.

---

## Net Phase 1 deltas to plan

These items **not** previously enumerated as discrete tasks need to be folded into the named phases:

1. **Phase 2:** rename event `v18.runtime.{started,completed}` → `runtime.{started,completed}` and add `validate_no_v18_event_strings` guard against future re-emission.
2. **Phase 2:** retitle HTML report `runtime/render.py:333` to v19 wording; add `validate_no_v18_html_branding` guard.
3. **Phase 6:** SLO leak fix — `runtime/slo.py:22` must not count `stub_delivered` as `delivery_ok` in `production` mode; new validator `validate_slo_stub_delivery_not_production_ok`.
4. **Phase 9:** sweep remaining `v18.7`/`v18` strings in `runtime/operating-discipline.md` and `runtime/failure_impl.py:89`.

All four deltas are minor — they slot into existing phase scopes without creating new phases.

---

## Sign-off

Phase 1 cross-cut investigations confirm:

- The **runtime executor gap** (Phase 3) is the largest single contributor to the operator-reported "10 runs, 0 real output" failure mode — `cmd_worker` does not iterate WU pending directory.
- The **outbox magic defaults** (Phase 4C T4C.6 — RAF/DFL=0.85/0.55, 0.7/0.3 thresholds) is the second largest — it lets a content-only run pass `citation_grounding_gate` without any real grounding.
- The **v18 emit set** (Phase 2 + 4C T4C.5) is mechanical; tests are easy.
- The **net-new modules** (`external_collect`, `work_units`, `legacy_compat`, etc.) must satisfy P0/P1 negative requirements from day one.

Phase 1 closed. Proceeding to Phase 2 — kill v18 emission.
