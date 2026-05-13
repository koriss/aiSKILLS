# Research Factory Orchestrator — v19 core operator sheet

**Version:** `19.4.7`  
**ADR:** `docs/adr/ADR-001-v19-pragmatic-rigor.md`  
**Runtime truth:** `docs/adr/ADR-015-runtime-truth-restoration.md`  
**Single funnel:** `docs/adr/ADR-019-single-dossier-funnel.md`

## Role

Host-invoked research orchestration skill: artifact-first compute, profile-driven validation, and delivery truth gating. **Delivery** (chat apps, email, etc.) is configured by the host; this repo stays compute + artifacts.

### IDE / agent registry (supported actions)

Use **only** the commands in **`SKILL.md` → Registry (IDE / coding agents)** for supported work from a git checkout + shell. **Research** = **`scripts/rfo_execute.py`** only; `validate_skill`, `unittest`, preflight, and post-run validators are separate **registry** actions, not alternate research CLIs. **`contracts/supported-skill-actions-v1.json`** duplicates the registry for tooling. Anything outside that table is **unsupported** unless you are following explicit troubleshooting notes in `docs/runtime-paths.md` (e.g. adapter emergency).

### What the host must supply

| Concern | Typical env / argv |
|--------|---------------------|
| Runs filesystem | Workspace-first: ``OPENCLAW_WORKSPACE_DIR`` / ``--workspace-root`` → ``<ws>/rfo-runs``; optional explicit ``--runs-root`` / ``RFO_RUNS_ROOT`` (deprecated; see ``runtime/config_resolution.py``) |
| JSON relay (bridge) | `RFO_WEB_SEARCH_JSON_API_BASE` or `--web-search-json-api-base` (**required** for canonical bridge; missing relay → **non-zero**, not silent stub) |
| Secondary relay (deprecated) | `RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE` — optional; if set, appears only in **`deprecated_inputs_used`** on the effective-config snapshot (not an operator-facing second “product path”) |
| Run profile | `RFO_RUN_PROFILE` or bridge `--profile` (**`dossier`** default; legacy names remap in `runtime.profiles`; see `docs/PROFILE_DEFAULTS.md`) |
| User-agent strings | Optional `RFO_WEB_SEARCH_USER_AGENT` (defaults are neutral; no vendor URL) |
| Wikipedia URL heuristic (bridge) | `RFO_WIKIPEDIA_HEURISTIC=1` to treat `wikipedia.org` as raw-document |
| Operator diagnostics | ``python3 -S scripts/rfo_execute.py --preflight …`` prints ``effective-config`` JSON (stdout); forbidden env keys (e.g. ``RFO_SMOKE``) force exit **2** |
| Container path hints | `RFO_HOST_WORKSPACE_ROOT` + `RFO_CONTAINER_WORKSPACE_PREFIX` (both optional; prefix required if mapping) |

## Eight-phase pipeline

1. Intake
2. Context
3. Acquisition
4. Synthesis
5. Contradiction scan
6. Final answer gate
7. Validation
8. Delivery

## Sacred path

Every factual claim must trace through claim -> evidence -> source with explicit ids.

## V1–V6

- V1 `validate_artifact_schema`: artifacts parse and satisfy v19 schema.
- V2 `validate_traceability`: sacred path consistency.
- V3 `validate_source_quality`: source role and independence constraints.
- V4 `validate_claim_status`: claim status, caps, contradiction guards.
- V5 `validate_final_answer`: risk blocks and final gate semantics.
- V6 `validate_delivery_truth`: artifact/delivery consistency and no fake delivery.
- **Citation grounding** (`validate_citation_grounding`): when the profile’s `active_validators` includes it (see `validation-profiles/*.json`), `run_core_validators.py` runs it after V6; missing `citation-grounding-result.json` is a **warning-only pass** on profiles that do not require web/collection grounding. For host agents that embed long claim/snippet text separately from RFO’s RAF math, apply `prompts/host-agent-embedding-truncate.md` (truncate before embed).

## Profiles

- **`dossier`** — single production funnel (relay packet required, stubs disallowed for real research).
- Fixture harness JSON under `validation-profiles/`: **`search-primary`**, **`propaganda-io`**, **`book-verification`** (inherit options from **`dossier`** via `parent_profile` where present).

Run:

`python -S scripts/run_core_validators.py --run-dir <run_dir> --profile dossier`

## Queue diagnostics (runs-root)

Canonical layout: ``<runs-root>/queue/{pending,running,done}/``.

- **Worker lease (single-flight lock):** ``<runs-root>/queue/worker.lease`` — **not** ``<runs-root>/worker.lease``.
  Inspect: ``ls -la <runs-root>/queue/worker.lease``, ``stat``, ``cat`` (contains JSON with ``pid``, ``job_file``, ``created_at``).
- **Stale lease:** if no ``runtime_job_worker`` is running but claims stay blocked, TTL-based cleanup applies when **`RFO_WORKER_LEASE_STALE_SECONDS`** (default ``900``) is **> 0** and file age exceeds TTL; operators may delete the lease file manually after verifying no active worker PID.
- **`lease_present` retries:** prefetch bridge repeats worker until claim; error text references ``queue/worker.lease``.
- **Stuck ``running/` jobs:** if ``runtime-status.json`` has ``state: failed`` or JSON still has ``status: queued`` while the file sits under ``queue/running/``, run::
  ```bash
  python3 -S scripts/rfo_queue_recover.py --runs-root <runs-root>
  ```

## Relay / web search defaults (SearXNG-style)

Environment overrides (unset = use builtin defaults where noted):

| Variable | Default | Notes |
| --- | --- | --- |
| `RFO_WEB_SEARCH_SAFESEARCH` | `1` | Relay query param ``safesearch`` |
| `RFO_WEB_SEARCH_DEFAULT_ENGINES` | `google` | Used when `RFO_WEB_SEARCH_ENGINES` is unset |
| `RFO_WEB_SEARCH_ENGINES` | — | If set, overrides default engines entirely |
| `RFO_WEB_SEARCH_LANGUAGE` | — | Relay ``language`` when set |
| `RFO_WEB_SEARCH_FETCH_CAP` | `20` | Max rows requested before rerank/trim |
| `RFO_SEARCH_REL_REQUIRE_TOKEN_MATCH` | unset | Set to ``1`` to drop zero-token-match rows when enough remain |

## Logical consistency (LC01–LC16)

`scripts/validate_logical_consistency.py` remains an explicit parallel gate for release/failure-corpus workflows.
