---
name: research_factory_orchestrator
description: Research Factory Orchestrator — v19.4.6+ artifact-only compute with profile-driven validation (V1–V6 + citation grounding when required); user-visible delivery is always host-owned (stdout handoff or your gateway).
license: internal
metadata:
  version: "19.4.6"
  package: research-factory-orchestrator
  command: "/research_factory_orchestrator"
  entrypoint: "scripts/interface_runtime_adapter.py"
  native_relay_entrypoint: "scripts/rfo_execute.py"
  native_relay_bridge_impl: "scripts/run_rfo_with_web_search.py"
  runtime_worker: "scripts/runtime_job_worker.py"
  delivery_worker: "scripts/outbox_delivery_worker.py"
  discovery_required: true
  release: "19.4.6"
---

## HOW TO OPERATE THIS SKILL

Primary operator sheet lives in `SKILL-core.md`. This file is the thin v19 overlay and execution contract.

### Preflight (disk-backed truth)

- Read this file through **Artifacts / gates** before promising a finished investigation.
- After any run: open **`report/full-report.html`** (or the profile’s primary artifact), then **`final-answer-gate.json`** and **`citation-grounding-result.json`** when the profile requires grounding; do not narrate a final verdict from relay snippets alone.
- Do not confuse **CLI `stub_delivered`** with **host gateway delivery** (confirmed attachments / ack path); read `delivery-manifest.json` + provider acks for the shell you actually used.

### Allowed execution paths

- **Host slash / native command (canonical research)** — the host runs **`python3 -S scripts/rfo_execute.py`** (thin façade: loads the bridge implementation module internally; **sequential** relay query expansion + **`research/research-plan.json`** on disk + collectors + queue bridge — **not** a multi-agent swarm; see `docs/design/RFO-SEQUENTIAL-SEARCH-NO-MULTI-AGENT.md` and `docs/adr/ADR-021-research-plan-disk-sequential-relay.md`). **Primary human artifact:** **`report/full-report.html`**. Plan mode: **`RFO_RESEARCH_PLAN_MODE=off|llm_v1`** (default `off`). Preallocated run reuse: **`RFO_PREALLOCATED_RUN_DIR`** (set by the bridge; do not hand-craft for production slash). Delivery stays host-owned (stdout handoff / gateway). See `docs/runtime-paths.md`.
- **Queue / tooling (not standalone research):** `python3 -S scripts/interface_runtime_adapter.py adapter --runs-root <runs-root> --interface cli --provider cli --task "..."` — preallocated run-dir / CLI queue plumbing only; not the native slash research path.
- **`scripts/run_rfo_full_research.py`** — **retired** as `__main__` (stderr → **`rfo_execute.py`**, exit **2**). Test helpers live in **`runtime/standalone_relay_driver.py`** — not an operator path.
- `python3 -S scripts/runtime_job_worker.py --runs-root <runs-root> --execute-runtime`
- `python3 -S scripts/outbox_delivery_worker.py --runs-root <runs-root>`
- **`scripts/run_research_factory.py`** — **retired** as `__main__` (stderr → **`rfo_execute.py`**, exit **2**). Workers use **`rfo_runtime_core.py`** directly; this shim is not research launch.

### Registry (IDE / coding agents)

| Action | Command (from skill root) |
|--------|-------------------------|
| **Research (relay + queue)** | `python3 -S scripts/rfo_execute.py --runs-root … --task "…"` (+ relay base env or `--web-search-json-api-base`) |
| **Preflight / effective-config** | `python3 -S scripts/rfo_execute.py --preflight …` — stdout: `rfo-effective-config-v1` JSON; schema: `contracts/rfo-effective-config-v1.schema.json` |
| **Skill packaging gate** | `python3 -S scripts/validate_skill.py` |
| **Unit tests** | `python3 -m unittest discover -s tests` |
| **Post-run validators** | `python3 -S scripts/run_core_validators.py --run-dir <run-dir> --profile <profile>` |

### Prohibitions

- Do not route `/research_factory_orchestrator` to a plain subagent. A chat-only recap or `memory/*.md` write-up is **not** RFO completion: there is no run-dir gate bundle, no `__OPENCLAW_SKILL_RESULT__` contract path, and no gateway-attested delivery. If the gateway killed the bridge (SIGTERM), the worker is wedged (`lease_present`), or the user only saw “busy” — triage with `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` and `latest_run/observability-events.jsonl` (`bridge.worker_poll`), not a replacement research thread.
- **Channel gotcha (Telegram / some clients):** if the user line is delivered to the model session as **plain `text`** (e.g. JSON `content: [{ "type": "text", "text": "/research_factory_orchestrator …" }]`) instead of **host native skill dispatch**, answering with `web_search` / `web_fetch` is **not** an RFO run — fix gateway slash registration and timeouts; see `docs/operators/openclaw-gateway-rfo-notes.md` § B0. To lint exports: `python3 -S scripts/validate_rfo_command_did_not_spawn_plain_subagent.py <path>`.
- Do not claim delivery without `delivery-manifest.json` + `attachment-ledger.json` + provider ack.
- Do not treat smoke/seed-only artifacts as completed production research.
- Do not publish local filesystem paths as proof of delivery.
- Do not save long HTML dumps as loose **`*.html`** in the workspace root — canonical **`report/full-report.html`** lives only under the **`run_dir`**; use **`*.md`** drafts inside that run-dir when scribbling intermediate prose.

### Runtime truth contract

- `final-answer-gate.json` must remain authoritative for user-visible completion claims.
- `run-mode-classification.json` decides whether output is `seed_only_smoke`.
- Manual fallback output must be explicitly marked and never presented as validated RFO completion.

### Product canon: depth vs naming

- **Canonical deep research** is the **`dossier`** bridge / work-unit pipeline (multi-step collectors, source packet, full validators). **`run_rfo_full_research.py`** is not an operator entrypoint; use **`rfo_execute.py`** for relay+queue depth.
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
- `docs/adr/ADR-021-research-plan-disk-sequential-relay.md`
