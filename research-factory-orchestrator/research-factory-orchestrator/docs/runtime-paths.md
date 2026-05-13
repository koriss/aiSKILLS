# RFO runtime entrypoints (one-page map)

This document fixes **vector F** (“which code path ran?”): a single checklist for operators and coding agents.

## Relay search shape (sequential, not multi-agent)

Relay **“fanout”** is **sequential**: `scripts/rfo_query_fanout.py` walks deterministic query templates and calls the JSON relay one query at a time, then merges/dedupes URLs. There is **no** in-process parallel fanout pool for those searches. Product wording: **`docs/design/RFO-SEQUENTIAL-SEARCH-NO-MULTI-AGENT.md`**.

## Research plan on disk (bridge)

- **Lifecycle:** `scripts/run_rfo_with_web_search.py` allocates **`run_dir`** immediately (`runtime.render.allocate`), bootstraps `research/` + `graph/` (`runtime.research_bridge_bootstrap`), then relay — so partial traces survive early failures (`research/bridge-phase-log.jsonl`).
- **`research/research-plan.json`:** versioned **`research-plan-v1`** (`contracts/research-plan-v1.schema.json`). **`RFO_RESEARCH_PLAN_MODE=off`** (default): plan mirrors template `build_query_vectors`; **`llm_v1`**: planner (`runtime/research_plan_planner.py`, `RFO_RESEARCH_PLANNER_*`) with schema repair + fallback; execution still **one sequential relay stream** (`fanout_relay_search` vs `fanout_relay_search_from_queries`).
- **Adapter handoff:** bridge sets **`RFO_PREALLOCATED_RUN_DIR=<run_dir>`** so `interface_runtime_adapter adapter` reuses the same directory (see **`docs/adr/ADR-021-research-plan-disk-sequential-relay.md`**).
- **`graph/wave-plan.json`:** materialized from the plan after relay for **`wave_graph_gate`** file presence in the bridge path.

## Canonical production entrypoint (relay + queue bridge)

**Prefer one command everywhere** (host compose, docs, mental model):

```bash
python3 -S scripts/rfo_execute.py --runs-root <workspace>/rfo-runs --task "<task>"
```

`scripts/rfo_execute.py` is a thin façade: it loads and runs **`scripts/run_rfo_with_web_search.py`** with the **same argv** and exit semantics. **Operator-facing docs and compose files** should invoke **`rfo_execute.py` only**; the bridge module name is an implementation detail.

**Preflight / effective config:** `python3 -S scripts/rfo_execute.py --preflight …` prints **`rfo-effective-config-v1`** JSON to **stdout** and exits **0** when relay + runs-root resolve cleanly, **2** when forbidden env keys are set or resolution fails — **no** run allocation. Snapshot shape is defined in **`contracts/rfo-effective-config-v1.schema.json`**. On a normal bridge run, after `allocate`, the run-dir includes **`effective-config.json`** with the same snapshot.

**Gateway timeout vs worker wait loop:** default `RFO_BRIDGE_WORKER_*` values and a pessimistic budget formula for the subprocess runner are documented in **`docs/operators/openclaw-gateway-rfo-notes.md`** (§ A3 + B1).

**Legacy / retired:** `scripts/run_rfo_full_research.py` — **not** an operator entrypoint; executing it prints a fatal hint pointing at **`rfo_execute.py`** and exits **2**. Shared test helpers: **`runtime/standalone_relay_driver.py`**. See § “Standalone relay driver” below.

## Native relay (host agent / gateway)

1. Operator invokes **`/research_factory_orchestrator <task>`** through the host UI (slash command).
2. **Native handler** in the host extension resolves the skill under `workspace/skills/research-factory-orchestrator/`.
3. **Bridge process (canonical argv):**  
   `python3 -S scripts/rfo_execute.py --runs-root <workspace>/rfo-runs --task "<task>"`  
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
- **Slash string in a normal user `text` part** (e.g. exported session: `content: [{ "type": "text", "text": "/research_factory_orchestrator …" }]`) means the host did **not** dispatch native skill compute for that turn — the model may still choose `web_search` / `web_fetch`. Fix channel/gateway routing; see **`docs/operators/openclaw-gateway-rfo-notes.md`** § **B0**.
- **When the bridge is slow or the worker is busy:** read **`docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`** (`queue/worker.lease`, `pending` vs `running`, PID). While the bridge waits, **`latest_run/observability-events.jsonl`** may contain **`bridge.worker_poll`** lines (`attempt`, `reason`, optional queue snapshot) — use them to explain “still RFO” vs “stuck”.
- **Host policy** (timeouts, whether to spawn a subagent on SIGTERM) lives in the gateway repo — see **`docs/operators/openclaw-gateway-rfo-notes.md`** for a checklist aligned with this skill’s contract.

The LLM must **not** invent ZIP paths, RAF numbers, or “sent to Telegram” without the rows above. Final user-visible truth is **`final-answer-gate.json`** plus the profile’s primary artifact (usually **`report/full-report.html`**).

### Bridge stdout/stderr (symmetry with execute)

Treat **`stdout`** from the bridge as **handoff-only:** the line **`__RFO_SKILL_AGENT_HANDOFF__=<json>`** (`HANDOFF_STDOUT_PREFIX` in `runtime/artifact_execute_impl.py`). Progress, **`[DONE]`**, and normalization logs belong on **`stderr`**. Parsing hosts should locate the capsule by prefix, not assume no other stdout during operator smoke runs. **`build_package`** after bridge MAY use **`quiet=True`** so packaging does not add JSON blobs to stdout. Detail: **`docs/adr/ADR-018-bridge-handoff-contract-and-portable-paths.md`**.

## Artifact-only CLI (`compute-only` execute)

1. Invocation: **`python3 -S -m runtime.artifact_execute_impl`** or **`scripts/interface_runtime_adapter.py execute --task … --runs-root …`** (per your wrapper).
2. **`cmd_execute` → `cmd_run` + `build_package` → `_build_manifest` + stdout handoff**.
3. No outbound channel logic in this layer; attaching files is the host’s responsibility.

## Standalone relay driver (`scripts/run_rfo_full_research.py`) — **retired from operators**

Historically a packaged **relay + fetch** CLI (not the native slash bridge). **Today:** the script is a **grave marker** only — stderr → **`rfo_execute.py`**, exit **2**. Claim/matrix/post-finish helpers used by tests live in **`runtime/standalone_relay_driver.py`**.

- **Tests:** import from **`runtime.standalone_relay_driver`** — that is **not** permission to run `run_rfo_full_research.py` for production.
- **Profile `search-primary`:** described in `contracts/run-profiles.json` for artifact semantics; **operator** relay+queue depth is **`rfo_execute.py`** (bridge implementation is loaded internally).

### `search-primary` profile: contradiction scan (E3)

- **`validation-profiles/search-primary.json`** is a **relay / smoke harness**: it keeps **`l0_contradiction_scan_not_performed_for_profile`** at **`warn`**, not block, and many “deep” narrative validators are off by design.
- Runs using this profile may therefore show **`contradiction_scan_performed: false`** / **`scan_scope: "none"`** in **`final-answer-gate.json`** defaults — **intentional out-of-scope** for fast fixture runs, **not** a silent failure of the dossier pipeline.
- For **full contradiction coverage**, use the **`dossier`** profile (bridge / worker) and the validators enabled there; do not “fix” search-primary to imply dossier semantics without renaming the profile.

## Legacy / auxiliary

- **`scripts/runtime_job_worker.py` / `outbox_delivery_worker.py`** — queued worker pipeline (not the v19.4 native slash path).
- **`scripts/run_research_factory.py`** — **not** an operator entrypoint; running as `__main__` prints a fatal hint → **`rfo_execute.py`**, exit **2** (provenance shim for contracts; workers call **`rfo_runtime_core.py`**).
- **HTML tooling:** **`scripts/rfo_render.py`** with subcommands `canonical` | `semantic-shell` (thin wrappers remain for backwards compatibility).

## Phased rollout (skill repo only)

Work is sequenced **inside this package** as: **(1)** operator docs + contracts + effective-config schema + markdown guardrails; **(2)** single resolver (`runtime/config_resolution.py`) + bridge/path_guard consumers + preflight; **(3)** legacy grave markers, forbidden-env enforcement in canonical paths, run-dir **`effective-config.json`** after allocate, tests for missing relay/workspace. **Gateway / host** changes (argv relay from the same config block as the agent’s web plugin) stay **outside** this tree per deploy ADRs.

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

## Production incident checklist (preflight)

**Context (guest agent / Telegram):** the model’s built-in `web_search` tool does **not** inject `RFO_WEB_SEARCH_JSON_API_BASE` into the RFO subprocess. You must pass the JSON relay **explicitly** (argv below or host-native slash wiring).

| Input | Required? | Notes |
|-------|-------------|--------|
| **Skill root / CWD** | Yes | Run from the **inner** package root where `scripts/rfo_execute.py` lives (`SKILL.md` tree). Skill root in snapshots comes from **`__file__`**, but operators should **`cd`** there to avoid wrong relative paths. |
| **`runs_root`** | Yes (or workspace) | e.g. `<OPENCLAW_WORKSPACE_DIR>/rfo-runs` or explicit `--runs-root` (deprecated env: see `runtime/config_resolution.py`). |
| **Relay base** | Yes | `--web-search-json-api-base "<url>"` **or** `RFO_WEB_SEARCH_JSON_API_BASE`. **Canonical:** no relay → **exit 2** on preflight and on bridge start — not a “successful” run without search and **not** a silent stub-only dossier. |
| **`skill_root`** | Derived | Shown in effective-config JSON for audits. |
| **Forbidden env** | Must be unset | `RFO_SMOKE`, `RFO_EXPERIMENT_BRIDGE`, `RFO_ALLOW_LEGACY*` → canonical preflight/bridge exits **2** (configuration error). |
| **Secondary relay** | Optional | `RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE` — deprecated; if set, appears only under **`deprecated_inputs_used`** in effective-config (not a second product path). |
| **Sync vs background** | Sync for preflight | Use **foreground** subprocess so exit code and stdout JSON are visible; do not hide failures behind `background=true` when the operator needs pass/fail. |

| Step | Command (example — substitute absolute paths) |
|------|---------|
| Resolve relay + runs-root without allocating | `cd /path/to/openclaw/workspace/skills/research-factory-orchestrator && python3 -S scripts/rfo_execute.py --preflight --runs-root /path/to/openclaw/workspace/rfo-runs --web-search-json-api-base "http://127.0.0.1:8180"` |
| Inspect | **stdout:** `rfo-effective-config-v1` JSON (`errors` must be empty; `relay` non-null). **Exit:** `0` ok, `2` forbidden env, missing relay, or resolution failure. |

**Do not** conflate **native `/research_factory_orchestrator`** (host dispatches bridge) with a **manual** shell from `skills/.../scripts` without the same argv/env — if RFO failed, report the **non-zero exit** and stderr; do not substitute a parallel “answer” from generic web tools and call it RFO.

Use this from a **guest agent** or broken-gateway triage before re-running a full task.

## Adapter emergency policy (queue tooling only)

`scripts/interface_runtime_adapter.py adapter` exists for **preallocated run-dir reuse** and **CLI queue** workflows. It is **not** a drop-in replacement for **`rfo_execute.py`** on the native `/research_factory_orchestrator` path: hosts that route slash compute only through adapter argv skip the documented bridge contract unless they also satisfy disk gates (`result-manifest.json`, validator bundle). Prefer fixing gateway argv to **`rfo_execute.py`**; see **`docs/adr/ADR-016-compute-vs-delivery-split.md`**.

## Observability (`errors.jsonl`, vector K)

- **`severity: warning`** events (for example **`EXTERNAL-COLLECTION-NO-SEEDS`** under dossier/external-off without **`RFO_SEED_URLS`**) are **not** necessarily pipeline failure; distinguish them from **`failed`**/`exit≠0`/missing triple deliverables in triage.
