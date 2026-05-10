# RFO runtime entrypoints (one-page map)

This document fixes **vector F** (“which code path ran?”): a single checklist for operators and coding agents.

## Native relay (host agent / gateway)

1. Operator invokes **`/research_factory_orchestrator <task>`** through the host UI (slash command).
2. **Native handler** in the host extension resolves the skill under `workspace/skills/research-factory-orchestrator/`.
3. **Bridge process:**  
   `python3 -S scripts/run_rfo_with_web_search.py --runs-root <workspace>/rfo-runs --task "<task>"`  
   (+ relay env / `--web-search-json-api-base` as deployed).  
   This is **not** `scripts/interface_runtime_adapter.py` for the slash-command path.
4. Worker / collector stages inside the bridge write the run-dir; **`render_all`** may re-render HTML; **`ensure_canonical_full_report_html`** + **`emit_agent_skill_handoff`** finalize `report/full-report.html` and **`result-manifest.json`**.
5. **Host delivery:** the gateway reads **`marker.run_dir`** + manifest from the handoff and attaches artifacts / chunked text to the operator channel (implementation is host-owned).

### Bridge stdout/stderr (symmetry with execute)

Treat **`stdout`** from the bridge as **handoff-only:** the line **`__RFO_SKILL_AGENT_HANDOFF__=<json>`** (`HANDOFF_STDOUT_PREFIX` in `runtime/artifact_execute_impl.py`). Progress, **`[DONE]`**, and normalization logs belong on **`stderr`**. Parsing hosts should locate the capsule by prefix, not assume no other stdout during operator smoke runs. **`build_package`** after bridge MAY use **`quiet=True`** so packaging does not add JSON blobs to stdout. Detail: **`docs/adr/ADR-018-bridge-handoff-contract-and-portable-paths.md`**.

## Artifact-only CLI (`compute-only` execute)

1. Invocation: **`python3 -S -m runtime.artifact_execute_impl`** or **`scripts/interface_runtime_adapter.py execute --task … --runs-root …`** (per your wrapper).
2. **`cmd_execute` → `cmd_run` + `build_package` → `_build_manifest` + stdout handoff**.
3. No outbound channel logic in this layer; attaching files is the host’s responsibility.

## Legacy / auxiliary

- **`scripts/runtime_job_worker.py` / `outbox_delivery_worker.py`** — queued worker pipeline (not the v19.3 native slash path).
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

- **`severity: warning`** events (for example **`EXTERNAL-COLLECTION-NO-SEEDS`** under `live-bridge` without **`RFO_SEED_URLS`**) are **not** necessarily pipeline failure; distinguish them from **`failed`**/`exit≠0`/missing triple deliverables in triage.
