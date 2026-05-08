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
