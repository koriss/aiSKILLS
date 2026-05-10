---
name: research_factory_orchestrator
description: Research Factory Orchestrator — v19.3+ artifact-only compute with profile-driven V1–V6 validation; user-visible delivery is always host-owned (stdout handoff or your gateway).
license: internal
metadata:
  version: "19.3.1"
  package: research-factory-orchestrator
  command: "/research_factory_orchestrator"
  entrypoint: "scripts/interface_runtime_adapter.py"
  native_relay_entrypoint: "scripts/run_rfo_with_web_search.py"
  runtime_worker: "scripts/runtime_job_worker.py"
  delivery_worker: "scripts/outbox_delivery_worker.py"
  discovery_required: true
  release: "19.3.1"
---

## HOW TO OPERATE THIS SKILL

Primary operator sheet lives in `SKILL-core.md`. This file is the thin v19 overlay and execution contract.

### Allowed execution paths

- **Host slash / native command (if your agent exposes it)** — the **host** runs **`scripts/run_rfo_with_web_search.py`** (relay bridge + collectors). Delivery to the user stays **outside** this package (stdout marker, gateway, or other channel). See `docs/runtime-paths.md`.
- `python3 -S scripts/interface_runtime_adapter.py adapter --runs-root <runs-root> --interface cli --provider cli --task "..."`
- `python3 -S scripts/run_rfo_with_web_search.py --runs-root <runs-root> --web-search-json-api-base <relay-base-url> --task "..."` (default profile `live-bridge`; optional **`RFO_BRIDGE_RENDER_STRICT=1`** to fail closed if re-render throws)
- `python3 -S scripts/runtime_job_worker.py --runs-root <runs-root> --execute-runtime`
- `python3 -S scripts/outbox_delivery_worker.py --runs-root <runs-root>`
- `python3 -S scripts/run_research_factory.py --project-dir <run-dir> --task "..."`

### Prohibitions

- Do not route `/research_factory_orchestrator` to a plain subagent.
- Do not claim delivery without `delivery-manifest.json` + `attachment-ledger.json` + provider ack.
- Do not treat smoke/seed-only artifacts as completed production research.
- Do not publish local filesystem paths as proof of delivery.
- Do not save long HTML dumps as loose **`*.html`** in the workspace root — canonical **`report/full-report.html`** lives only under the **`run_dir`**; use **`*.md`** drafts inside that run-dir when scribbling intermediate prose.

### Runtime truth contract

- `final-answer-gate.json` must remain authoritative for user-visible completion claims.
- `run-mode-classification.json` decides whether output is `seed_only_smoke`.
- Manual fallback output must be explicitly marked and never presented as validated RFO completion.

### v19 core validation

- Prefer validation profile embedded in the run dir (`validation-profile-used.json`, `run-profile.json`); optionally override with `RFO_V19_PROFILE` (`mvr`, `full-rigor`, `propaganda-io`, `book-verification`).
- Run `python3 -S scripts/run_core_validators.py --run-dir <run-dir> --profile <profile>`.
- Core validator stack is V1..V6 with fail-closed delivery truth.

### References

- `docs/runtime-paths.md` — native relay vs artifact execute vs workers (single-page map).
- `docs/qa/RFO-FULL-RESEARCH-PLAYBOOK.md` — golden paths, relay steps, troubleshooting (links to SKILL-core / profiles, no duplicate env tables).
- `SKILL-core.md`
- `docs/v19/README.md`
- `docs/v19/validators-core.md`
- `docs/adr/ADR-001-v19-pragmatic-rigor.md`
- `docs/adr/ADR-015-runtime-truth-restoration.md`
