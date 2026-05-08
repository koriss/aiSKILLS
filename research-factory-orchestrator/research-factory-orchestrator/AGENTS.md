# AGENTS.md — RFO ≥ v19.2.1 honesty contract

This file defines the **only** allowed way for an agent (including the
guest agent inside `openclaw-cli`) to invoke Research Factory Orchestrator
(RFO). Violations are caught by `scripts/_rfo_path_guard.py` at process
start and by `tools/verify_openclaw_run.py` after a run finishes.

## Canonical entrypoint

```bash
cd ~/.openclaw/workspace/skills/research-factory-orchestrator && \
  python3 -S scripts/interface_runtime_adapter.py \
    --runs-root ~/.openclaw/workspace/rfo-runs \
    --interface telegram --provider telegram \
    --chat-id "$TELEGRAM_INCOMING_CHAT_ID" \
    --reply-to-message-id "$TELEGRAM_INCOMING_MESSAGE_ID" \
    --api-base "${TELEGRAM_API_BASE:-https://api.telegram.org}" \
    --task "<user request as a single string>"
```

`$TELEGRAM_INCOMING_CHAT_ID` and `$TELEGRAM_INCOMING_MESSAGE_ID` MUST be
extracted from the incoming Telegram update by the host (e.g.
`openclaw-gateway`) and passed as argv to the adapter. They MUST NOT be
inherited from the environment.

## Worker pipeline

```bash
cd ~/.openclaw/workspace/skills/research-factory-orchestrator && \
  python3 -S scripts/runtime_job_worker.py    --runs-root ~/.openclaw/workspace/rfo-runs --execute-runtime
cd ~/.openclaw/workspace/skills/research-factory-orchestrator && \
  python3 -S scripts/outbox_delivery_worker.py --runs-root ~/.openclaw/workspace/rfo-runs
```

**Important:** `runtime_job_worker` only consumes `queue/pending/*.json`. Starting the worker alone (with no prior `interface_runtime_adapter adapter` enqueue) usually does nothing useful (`claimed:false`). The worker subprocess must inherit the same environment the run needs (e.g. `RFO_SOURCE_PACKET` when using a source packet).

## Web search + SearXNG (canonical)

Full external collection via SearXNG + `RFO_SOURCE_PACKET` + real queue + worker:

1. Build / obtain a source packet (JSON with `sources[]`) and set `RFO_SOURCE_PACKET` to its **file path** for the worker process.
2. **Enqueue** with `interface_runtime_adapter adapter` using `--runs-root` and `--task`. For routing metadata into Telegram delivery adapters use `--interface telegram` + `--provider telegram` plus host-supplied `--chat-id` / `--reply-to-message-id` (those fields are host concerns, not chat sends from the skill). For compute-only enqueue use `--interface cli --provider cli`.
3. Run `runtime_job_worker.py --runs-root … --execute-runtime` (env must still include `RFO_SOURCE_PACKET` so the nested `rfo_runtime_core run` inherits it).

Bundled bridge (implements 1–3 and post-steps) for operators:

```bash
cd ~/.openclaw/workspace/skills/research-factory-orchestrator && \
  python3 -S scripts/run_rfo_with_web_search.py \
    --runs-root ~/.openclaw/workspace/rfo-runs \
    --task "<user request>" \
    [--profile mvr]
```

The bridge ends with stdout line **`__RFO_SKILL_AGENT_HANDOFF__=<json>`** plus `instructions_for_invoking_agent` inside that JSON — the **caller** consumes it and replies to whichever channel applies. This skill performs no outbound messaging. Optional `outbox_delivery_worker.py` remains a separate host/ops process when you deliberately want Telegram send from infra, not default from bridge.

### Contract boundary (Adapter | Queue | Worker | Collector)

- **Adapter** (`cmd_adapter`): allocates `runs/<label>/`, writes `jobs/runtime-job.json`, appends index, drops `queue/pending/<job_id>.json`.
- **Queue**: `pending` → `running` → `done` (worker moves files + `worker.lease`).
- **Worker** (`cmd_worker`): claims one pending job, runs `rfo_runtime_core run` **inheriting the current OS environment**, then packaging / outbox prep.
- **Collector** (`collect`): reads `RFO_SOURCE_PACKET` file if present (`external_source_packet_loaded`); `RFO_SEED_URLS` probes are a separate branch. Breaking env inheritance (e.g. `subprocess.run(..., env={})` without merge) silently drops packets.

## BATS embeddings index (OpenClaw ops)

Failures such as **BATS 33/34 “embeddings index”** concern how much workspace memory OpenClaw indexes for tests, not RFO collector code. Mitigations: widen the indexed corpus (more eligible source files), adjust the indexer include policy, or change the embeddings threshold in the BATS scenario—treat as **platform ops**, orthogonal to collection truth flags.

## Hard prohibitions (enforced by code, not by convention)

| Violation | Where it is caught | Exit code / error |
| --- | --- | --- |
| Running from `*.bak*`, `*.old*`, `*~*`, `*.disabled`, `*.backup`, `copy of *` directories | `_rfo_path_guard.enforce_canonical_skill_path` | exit 11, `RFO-NON-CANONICAL-SKILL-PATH` |
| `--runs-root /tmp/...` without `RFO_ALLOW_TMP_RUNS_ROOT=1` | `_rfo_path_guard.enforce_runs_root_argv` | exit 12, `RFO-RUNS-ROOT-FORBIDDEN` |
| Invoking adapter without `--chat-id` and without `RFO_ALLOW_ENV_CHAT_ID=1` | `providers/telegram/telegram_delivery_adapter._resolve_routing` | `LIE-DETECTED-DELIVERY-STUB-WITHOUT-CONSENT` in `runtime/errors.jsonl`, `external_delivery_gate.status="delivery_not_proven"` |
| Calling adapter from a non-canonical skill name (basename ≠ `research-factory-orchestrator`) | `_rfo_path_guard.enforce_canonical_skill_path` | exit 11, `RFO-NON-CANONICAL-SKILL-PATH` |
| Narrating a `version` (e.g. "RFO v19.2.1 …") **before** reading `entrypoint-proof.json` or `run.json` from the actual run | `tools/verify_openclaw_run.py` (`LIE-DETECTED-NARRATIVE-WITHOUT-EVIDENCE`) | verifier non-zero exit |
| Claiming `real_external_delivery=true` while artifacts show `seed_only=true` or `delivery_not_proven` | `tools/verify_openclaw_run.py` | verifier non-zero exit |

## Smoke / consent escape hatches

These environment variables are accepted **only** for explicit smoke testing.
They MUST be unset in production guest-agent contexts:

- `RFO_ALLOW_TMP_RUNS_ROOT=1` — allows `--runs-root` under `/tmp` for
  ephemeral local smokes.
- `RFO_ALLOW_ENV_CHAT_ID=1` — allows the adapter to fall back to
  `TELEGRAM_CHAT_ID` from environment when `--chat-id` was not provided.
  The resulting ack records `chat_id_source="env_consent"` so the verifier
  can see this was a consented headless smoke.

`TELEGRAM_BOT_TOKEN` is always read from environment — that's normal.
`TELEGRAM_API_BASE` may come from argv (`--api-base`),
`interface-request.json`, env, or fallback to `https://api.telegram.org`.

## Why this contract exists

In RUN-36a7dcf7afd7 (v19.1.0) the guest agent invoked RFO from a leftover
`*.bak-…` directory with `--runs-root /tmp/rfo-runs` and without any
`chat_id`, producing a "successful" stub-only delivery while the narrative
spoke about real research. The `_rfo_path_guard` and the
`telegram_delivery_adapter` v19.2.1 hardening together make that scenario
physically impossible: the agent either runs from the canonical path with
real routing data, or it gets a structured refusal it cannot hide.
