---
name: research_factory_orchestrator
description: Research Factory Orchestrator — v19.4.3+ artifact-only compute with profile-driven validation (V1–V6 + citation grounding when required); user-visible delivery is always host-owned (stdout handoff or your gateway).
license: internal
metadata:
  version: "19.4.3"
  package: research-factory-orchestrator
  command: "/research_factory_orchestrator"
  entrypoint: "scripts/interface_runtime_adapter.py"
  native_relay_entrypoint: "scripts/rfo_execute.py"
  native_relay_bridge_impl: "scripts/run_rfo_with_web_search.py"
  runtime_worker: "scripts/runtime_job_worker.py"
  delivery_worker: "scripts/outbox_delivery_worker.py"
  discovery_required: true
  release: "19.4.3"
---

## HOW TO OPERATE THIS SKILL

Primary operator sheet lives in `SKILL-core.md`. This file is the thin v19 overlay and execution contract.

### Preflight (disk-backed truth)

- Read this file through **Artifacts / gates** before promising a finished investigation.
- After any run: open **`report/full-report.html`** (or the profile’s primary artifact), then **`final-answer-gate.json`** and **`citation-grounding-result.json`** when the profile requires grounding; do not narrate a final verdict from relay snippets alone.
- Do not confuse **CLI `stub_delivered`** with **host gateway delivery** (confirmed attachments / ack path); read `delivery-manifest.json` + provider acks for the shell you actually used.

### Allowed execution paths

- **Host slash / native command (canonical)** — the host runs **`python3 -S scripts/rfo_execute.py`** (thin façade → same argv/semantics as **`scripts/run_rfo_with_web_search.py`**: relay fanout + collectors + queue bridge). **Primary human artifact:** **`report/full-report.html`**. Delivery stays host-owned (stdout handoff / gateway). See `docs/runtime-paths.md`.
- `python3 -S scripts/interface_runtime_adapter.py adapter --runs-root <runs-root> --interface cli --provider cli --task "..."`
- `python3 -S scripts/run_rfo_with_web_search.py …` — **alias** of `rfo_execute.py` for operators who already embed this path; prefer **`rfo_execute.py`** in new docs and compose files.
- `python3 -S scripts/run_rfo_full_research.py …` — **legacy** standalone relay+fetch (blocked unless `RFO_ALLOW_LEGACY_ENTRYPOINT=1` or `--allow-legacy-entrypoint`). Profile **`search-primary`** when `RFO_RUN_PROFILE` unset; **not** dossier depth — see `docs/runtime-paths.md` appendix.
- `python3 -S scripts/runtime_job_worker.py --runs-root <runs-root> --execute-runtime`
- `python3 -S scripts/outbox_delivery_worker.py --runs-root <runs-root>`
- `python3 -S scripts/run_research_factory.py --project-dir <run-dir> --task "..."`

### Prohibitions

- Do not route `/research_factory_orchestrator` to a plain subagent. A chat-only recap or `memory/*.md` write-up is **not** RFO completion: there is no run-dir gate bundle, no `__OPENCLAW_SKILL_RESULT__` contract path, and no gateway-attested delivery. If the gateway killed the bridge (SIGTERM), the worker is wedged (`lease_present`), or the user only saw “busy” — triage with `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` and `latest_run/observability-events.jsonl` (`bridge.worker_poll`), not a replacement research thread.
- Do not claim delivery without `delivery-manifest.json` + `attachment-ledger.json` + provider ack.
- Do not treat smoke/seed-only artifacts as completed production research.
- Do not publish local filesystem paths as proof of delivery.
- Do not save long HTML dumps as loose **`*.html`** in the workspace root — canonical **`report/full-report.html`** lives only under the **`run_dir`**; use **`*.md`** drafts inside that run-dir when scribbling intermediate prose.

### Runtime truth contract

- `final-answer-gate.json` must remain authoritative for user-visible completion claims.
- `run-mode-classification.json` decides whether output is `seed_only_smoke`.
- Manual fallback output must be explicitly marked and never presented as validated RFO completion.

### Product canon: depth vs naming

- **Canonical deep research** is the **`dossier`** bridge / work-unit pipeline (multi-step collectors, source packet, full validators). Treat **`run_rfo_full_research.py`** as a **narrow relay+fetch driver** for smoke / CI / host shells that need JSON artifacts quickly — not a substitute for dossier depth, even though the script name contains “full”.
- Do not invent “depth flags” as a separate product surface; prefer the profile + run-mode classification already on disk.

### v19 core validation

- Prefer validation profile embedded in the run dir (`validation-profile-used.json`, `run-profile.json`); optionally override with `RFO_V19_PROFILE` — only **`dossier`**, **`search-primary`**, **`propaganda-io`**, **`book-verification`** (see `runtime/validate_impl.py`); unknown values are ignored for the v19 runner path.
- Run `python3 -S scripts/run_core_validators.py --run-dir <run-dir> --profile <profile>`.
- Core validator stack is V1..V6 with fail-closed delivery truth.

### References

- `docs/runtime-paths.md` — native relay vs artifact execute vs workers (single-page map); subagent vs native RFO.
- `docs/operators/openclaw-gateway-rfo-notes.md` — timeouts / fallback policy (host deploy; checklist).
- `docs/adr/ADR-020-vacuum-of-agency-degraded-modes.md` — why plain fallback fights the contract.
- `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` — `lease_present`, stuck `pending`, worker PID triage.
- `docs/qa/RFO-FULL-RESEARCH-PLAYBOOK.md` — golden paths, relay steps, troubleshooting (links to SKILL-core / profiles, no duplicate env tables).
- `docs/qa/TELEGRAM-LONGFORM-OUTPUT.md` — оформление длинных сообщений под Telegram списками/секциями без md-таблиц (доставка остаётся на стороне хоста по ADR-016).
- `SKILL-core.md`
- `docs/v19/README.md`
- `docs/v19/validators-core.md`
- `docs/adr/ADR-001-v19-pragmatic-rigor.md`
- `docs/adr/ADR-015-runtime-truth-restoration.md`
- `docs/adr/ADR-019-single-dossier-funnel.md`
