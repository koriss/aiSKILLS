# AGENTS.md — RFO ≥ v19.2.1 honesty contract

This file defines an **allowed** pattern for agents invoking Research Factory Orchestrator (RFO). Path guards (`scripts/_rfo_path_guard.py`) enforce canonical skill layout and approved `--runs-root` values; post-run checks may use `scripts/verify_skill_run_claims.py` (compatibility filename: `scripts/verify_openclaw_run.py`).

## What you must parameterize (any host)

| Variable / flag | Role |
|-----------------|------|
| `<SKILL_ROOT>` | Directory containing this package (`research-factory-orchestrator/`). |
| `RFO_RUNS_ROOT` or `--runs-root` | Persistent runs queue root (see `docs/adr/ADR-RFO_PORTABLE.md`). |
| Relay / bridge | `RFO_WEB_SEARCH_JSON_API_BASE` when using **`scripts/rfo_execute.py`** (canonical façade → `run_rfo_with_web_search.py`). |

## Canonical entrypoint (template)

```bash
cd <SKILL_ROOT> && \
  python3 -S scripts/interface_runtime_adapter.py \
    adapter --runs-root "${RFO_RUNS_ROOT}" \
    --interface cli --provider cli \
    --task "<user request as a single string>"
```

### Example: host-agnostic paths

```bash
cd <SKILL_ROOT> && \
  python3 -S scripts/interface_runtime_adapter.py \
    adapter --runs-root <RUNS_ROOT> \
    --interface cli --provider cli \
    --task "<user request as a single string>"
```

Optional argv `--chat-id`, `--reply-to-message-id`, `--api-base` are stored under
`interface/interface-request.json` for the **host** only; this repository does not
implement outbound messaging to external channels.

## Worker pipeline

```bash
cd <SKILL_ROOT> && \
  python3 -S scripts/runtime_job_worker.py    --runs-root <RUNS_ROOT> --execute-runtime
cd <SKILL_ROOT> && \
  python3 -S scripts/outbox_delivery_worker.py --runs-root <RUNS_ROOT>
```

**Important:** `runtime_job_worker` only consumes `queue/pending/*.json`. Starting the worker alone (with no prior `interface_runtime_adapter adapter` enqueue) usually does nothing useful (`claimed:false`). The worker subprocess must inherit the same environment the run needs (e.g. `RFO_SOURCE_PACKET` when using a source packet).

## Web search + JSON relay bridge

Full external collection uses a configurable HTTP JSON relay (SearxNG-style
`/search?q=…&format=json`) plus `RFO_SOURCE_PACKET`, the queue, and the worker:

1. Build / obtain a source packet (JSON with `sources[]`) or run the prefetch bridge (`scripts/rfo_execute.py`), which writes `RFO_SOURCE_PACKET`.
2. **Enqueue** with `interface_runtime_adapter.py adapter` using `--runs-root`, `--task`, and profile-related env as needed (`RFO_RUN_PROFILE`, etc.). Prefer `--interface cli --provider cli` for artifact-only enqueue.
3. Run `runtime_job_worker.py --runs-root … --execute-runtime` (env must include `RFO_SOURCE_PACKET` when using a prefetch packet so nested `rfo_runtime_core run` inherits it).

Bundled bridge (prefetch + queue + worker + handoff):

```bash
cd <SKILL_ROOT> && \
  python3 -S scripts/rfo_execute.py \
    --runs-root <RUNS_ROOT> \
    --web-search-json-api-base "${RFO_WEB_SEARCH_JSON_API_BASE:?set relay base URL}" \
    --task "<user request>"
```

Defaults: **`--profile dossier`** (sequential relay query expansion + source packet contract). `runtime.profiles.resolve` is fail-closed: only keys from `contracts/run-profiles.json` (`dossier`, `search-primary`); unknown `RFO_RUN_PROFILE` / CLI `--profile` raises `ValueError`.

The bridge exits non-zero if the relay base URL is missing. It ends with stdout line **`__RFO_SKILL_AGENT_HANDOFF__=<json>`** plus `instructions_for_invoking_agent` — the **caller** performs any user-visible send outside this repo. `outbox_delivery_worker.py` only runs provider adapters shipped here (`providers/cli`, `providers/webhook`); missing adapters yield failed acks, not silent “sent”.

### Contract boundary (Adapter | Queue | Worker | Collector)

- **Adapter** (`cmd_adapter`): allocates `runs/<label>/`, writes `jobs/runtime-job.json`, appends index, drops `queue/pending/<job_id>.json`.
- **Queue**: `pending` → `running` → `done` (worker moves files under `queue/` and acquires **`queue/worker.lease`** — not `runs-root/worker.lease`).
- **Recovery**: `python3 -S scripts/rfo_queue_recover.py --runs-root <runs-root>` moves inconsistent `queue/running/*.json` back to `pending/` when runtime failed or inner `status` is still `queued`.
- **Worker** (`cmd_worker`): claims one pending job, runs `rfo_runtime_core run` **inheriting the current OS environment**, then packaging / outbox prep.
- **Collector** (`collect`): reads `RFO_SOURCE_PACKET` file if present (`external_source_packet_loaded`); `RFO_SEED_URLS` probes are a separate branch. Breaking env inheritance (e.g. `subprocess.run(..., env={})` without merge) silently drops packets.

## BATS embeddings index (host platform ops)

Failures such as **BATS 33/34 “embeddings index”** concern how much workspace memory the host platform indexes for tests, not RFO collector code. Mitigations: widen the indexed corpus (more eligible source files), adjust the indexer include policy, or change the embeddings threshold in the BATS scenario—treat as **platform ops**, orthogonal to collection truth flags.

## Hard prohibitions (enforced by code, not by convention)

| Violation | Where it is caught | Exit code / error |
| --- | --- | --- |
| Running from `*.bak*`, `*.old*`, `*~*`, `*.disabled`, `*.backup`, `copy of *` directories | `_rfo_path_guard.enforce_canonical_skill_path` | exit 11, `RFO-NON-CANONICAL-SKILL-PATH` |
| `--runs-root /tmp/...` without `RFO_ALLOW_TMP_RUNS_ROOT=1` | `_rfo_path_guard.enforce_runs_root_argv` | exit 12, `RFO-RUNS-ROOT-FORBIDDEN` |
| Outbox event naming a provider with no `providers/<provider>/<provider>_delivery_adapter.py` | `runtime/outbox_impl.cmd_outbox` | ack `failed`, reason `PROVIDER-DELIVERY-ADAPTER-MISSING`, `delivery_not_proven` where applicable |
| Calling adapter from a non-canonical skill name (basename ≠ `research-factory-orchestrator`) | `_rfo_path_guard.enforce_canonical_skill_path` | exit 11, `RFO-NON-CANONICAL-SKILL-PATH` |
| Narrating a `version` (e.g. "RFO v19.2.1 …") **before** reading `entrypoint-proof.json` or `run.json` from the actual run | `scripts/verify_skill_run_claims.py` (`LIE-DETECTED-NARRATIVE-WITHOUT-EVIDENCE`) | verifier non-zero exit |
| Claiming `real_external_delivery=true` while artifacts show `seed_only=true` or `delivery_not_proven` | `scripts/verify_skill_run_claims.py` | verifier non-zero exit |

## Smoke / consent escape hatches

These environment variables are accepted **only** for explicit smoke testing.
They SHOULD be unset in production guest-agent contexts:

- `RFO_ALLOW_TMP_RUNS_ROOT=1` — allows `--runs-root` under `/tmp` for ephemeral local smokes.

## Why this contract exists

In RUN-36a7dcf7afd7 (v19.1.0) the guest agent invoked RFO from a leftover
`*.bak-…` directory with `--runs-root /tmp/rfo-runs` and narrated completion
without honest delivery proof. `_rfo_path_guard` and strict manifest checks
narrow that failure mode; handoff stays on disk and stdout so the host, not this
skill, owns user-visible replies.
