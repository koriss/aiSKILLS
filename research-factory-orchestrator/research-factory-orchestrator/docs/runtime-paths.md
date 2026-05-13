# RFO runtime entrypoints (one-page map)

This document fixes **vector F** (“which code path ran?”): a single checklist for operators and coding agents.

## Canonical production entrypoint (relay + queue bridge)

**Prefer one command everywhere** (host compose, docs, mental model):

```bash
python3 -S scripts/rfo_execute.py --runs-root <workspace>/rfo-runs --task "<task>"
```

`scripts/rfo_execute.py` is a thin façade: it loads and runs **`scripts/run_rfo_with_web_search.py`** with the **same argv** and exit semantics. Existing deployments that still invoke `run_rfo_with_web_search.py` directly remain valid; new text should standardize on **`rfo_execute.py`**.

**Gateway timeout vs worker wait loop:** default `RFO_BRIDGE_WORKER_*` values and a pessimistic budget formula for the subprocess runner are documented in **`docs/operators/openclaw-gateway-rfo-notes.md`** (§ A3 + B1).

**Legacy / dev-only:** `scripts/run_rfo_full_research.py` — standalone relay+fetch **without** the same queue bridge invariants; **blocked** unless `RFO_ALLOW_LEGACY_ENTRYPOINT=1` or `--allow-legacy-entrypoint` (exit **64** otherwise). See § “Standalone relay driver” below.

## Native relay (host agent / gateway)

1. Operator invokes **`/research_factory_orchestrator <task>`** through the host UI (slash command).
2. **Native handler** in the host extension resolves the skill under `workspace/skills/research-factory-orchestrator/`.
3. **Bridge process (canonical argv):**  
   `python3 -S scripts/rfo_execute.py --runs-root <workspace>/rfo-runs --task "<task>"`  
   (equivalent: `python3 -S scripts/run_rfo_with_web_search.py` with the same flags).  
   (+ relay env / `--web-search-json-api-base` as deployed).  
   This is **not** `scripts/interface_runtime_adapter.py` for the slash-command path.
4. Worker / collector stages inside the bridge write the run-dir; **`render_all`** may re-render HTML; **`ensure_canonical_full_report_html`** + **`emit_agent_skill_handoff`** finalize `report/full-report.html` and **`result-manifest.json`**.
5. **Host delivery:** the gateway reads **`marker.run_dir`** + manifest from the handoff and attaches artifacts / chunked text to the operator channel (implementation is host-owned).

## Delivery truth: native slash vs CLI / subagent

| Surface | Who proves user-visible delivery? | What to read on disk |
|--------|-------------------------------------|------------------------|
| **Native `/research_factory_orchestrator`** (gateway) | Host gateway + channel acks (`sendDocument`, audit JSONL). | `delivery-manifest.json`, `attachment-ledger.json`, host audit under `workspace/audit/`. |
| **`interface_runtime_adapter.py` + `--provider cli`** | **No** external channel — `stub_delivered` / `stub_only` is expected unless the operator wires a real provider. | Same manifests; treat `stub` as **not** Telegram proof. |
| **Plain subagent / chat-only recap** | **Invalid** as RFO completion — see `SKILL.md` prohibitions. | N/A — always open the run-dir artifacts. |

### Plain subagent vs native RFO (operator clarity)

- **Native RFO** ends with a **disk-backed run-dir**, `result-manifest.json` / stdout handoff contract, and (in production) gateway delivery + audit. The model is not the source of truth for “ZIP sent” or “investigation complete”.
- If the user only received a **Markdown file in workspace memory** or a narrative from **`sessions_spawn` / plain research**, that path **did not** run the validator gate bundle for that slash — treat it as **parallel chat research**, not a substitute for the run-dir.
- **When the bridge is slow or the worker is busy:** read **`docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`** (`queue/worker.lease`, `pending` vs `running`, PID). While the bridge waits, **`latest_run/observability-events.jsonl`** may contain **`bridge.worker_poll`** lines (`attempt`, `reason`, optional queue snapshot) — use them to explain “still RFO” vs “stuck”.
- **Host policy** (timeouts, whether to spawn a subagent on SIGTERM) lives in the gateway repo — see **`docs/operators/openclaw-gateway-rfo-notes.md`** for a checklist aligned with this skill’s contract.

The LLM must **not** invent ZIP paths, RAF numbers, or “sent to Telegram” without the rows above. Final user-visible truth is **`final-answer-gate.json`** plus the profile’s primary artifact (usually **`report/full-report.html`**).

### Bridge stdout/stderr (symmetry with execute)

Treat **`stdout`** from the bridge as **handoff-only:** the line **`__RFO_SKILL_AGENT_HANDOFF__=<json>`** (`HANDOFF_STDOUT_PREFIX` in `runtime/artifact_execute_impl.py`). Progress, **`[DONE]`**, and normalization logs belong on **`stderr`**. Parsing hosts should locate the capsule by prefix, not assume no other stdout during operator smoke runs. **`build_package`** after bridge MAY use **`quiet=True`** so packaging does not add JSON blobs to stdout. Detail: **`docs/adr/ADR-018-bridge-handoff-contract-and-portable-paths.md`**.

## Artifact-only CLI (`compute-only` execute)

1. Invocation: **`python3 -S -m runtime.artifact_execute_impl`** or **`scripts/interface_runtime_adapter.py execute --task … --runs-root …`** (per your wrapper).
2. **`cmd_execute` → `cmd_run` + `build_package` → `_build_manifest` + stdout handoff**.
3. No outbound channel logic in this layer; attaching files is the host’s responsibility.

## Standalone relay driver (`scripts/run_rfo_full_research.py`) — **legacy**

Packaged **relay + fetch** CLI (not the native slash bridge):

- **Entry:** requires `RFO_ALLOW_LEGACY_ENTRYPOINT=1` or `--allow-legacy-entrypoint`; otherwise prints stderr hint pointing at **`rfo_execute.py`** and exits **64**.

- Default profile is **`search-primary`** from `contracts/run-profiles.json` when `RFO_RUN_PROFILE` is empty (`runtime.profiles.resolve(..., entrypoint_default="search-primary")`).
- Uses **`fanout_relay_search`** (`scripts/rfo_query_fanout.py`, `contracts/query-fanout-config.json`) with stats recorded on **`collection-result.json`** (`relay_query_fanout`).
- Emits **`graph/wave-plan.json`** (so **`wave_graph_gate`** can pass on file presence), **`citation-grounding-result.json`**, **`feature-truth-matrix.json`** citation block, and a **`final-answer-gate.json`** aligned with those checks.
- **Not** the full **`dossier`** work-unit / source-packet pipeline; for that depth use **`scripts/rfo_execute.py`** (or **`runtime_job_worker.py`**). Delivery under **`cli`** may still be **`stub_only`** — distinguish from gateway-attested sends (ADR-016).

### `search-primary` profile: contradiction scan (E3)

- **`validation-profiles/search-primary.json`** is a **relay / smoke harness**: it keeps **`l0_contradiction_scan_not_performed_for_profile`** at **`warn`**, not block, and many “deep” narrative validators are off by design.
- Runs using this profile may therefore show **`contradiction_scan_performed: false`** / **`scan_scope: "none"`** in **`final-answer-gate.json`** defaults — **intentional out-of-scope** for fast fixture runs, **not** a silent failure of the dossier pipeline.
- For **full contradiction coverage**, use the **`dossier`** profile (bridge / worker) and the validators enabled there; do not “fix” search-primary to imply dossier semantics without renaming the profile.

## Legacy / auxiliary

- **`scripts/runtime_job_worker.py` / `outbox_delivery_worker.py`** — queued worker pipeline (not the v19.4 native slash path).
- **`scripts/run_research_factory.py`** — direct run-dir pipeline.
- **HTML tooling:** **`scripts/rfo_render.py`** with subcommands `canonical` | `semantic-shell` (thin wrappers remain for backwards compatibility).

## Bridge re-render strictness

- By default a failure in **`render_all`** inside **`run_rfo_with_web_search.py`** logs **`Re-render error (non-fatal)`** and still hands off (stale HTML possible).
- Set **`RFO_BRIDGE_RENDER_STRICT=1`** (or `true` / `yes`) to **abort before handoff** with exit **21**.

## Canonical report file

- **Path inside every run-dir:** `report/full-report.html`.
- **Writes** should go through **`runtime.report_html.write_canonical_full_report_html`** so MIME vs bytes stay aligned (see **`sniff_html_document`** / **`ensure_*`**).

## Agent hygiene (avoid vector B)

- Do **not** drop long **`*.html`** “reports” in the **workspace root**; host delivery only follows **`run_dir`** from the marker/manifest.
- Prefer **`*.md`** drafts **inside** the active run-dir (or a clearly marked scratch subtree), not ad-hoc HTML next to unrelated projects.

## Host vs container paths (vector J)

- Marker / `latest.json` may show a container workspace path while the host has a different mount prefix.
- Optional hint: **`RFO_HOST_WORKSPACE_ROOT`** + **`RFO_CONTAINER_WORKSPACE_PREFIX`** populate **`run_dir_host`** in manifest metadata (derivative; verify mounts).

## Observability (`errors.jsonl`, vector K)

- **`severity: warning`** events (for example **`EXTERNAL-COLLECTION-NO-SEEDS`** under dossier/external-off without **`RFO_SEED_URLS`**) are **not** necessarily pipeline failure; distinguish them from **`failed`**/`exit≠0`/missing triple deliverables in triage.
