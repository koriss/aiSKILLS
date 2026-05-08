# ADR-014 — Telegram operator control plane (historical)

## Status

**Superseded.** User-visible messaging and channel-specific proofing live in the
**host** (e.g. OpenClaw gateway). This skill is compute-only: artifacts +
**`__RFO_SKILL_AGENT_HANDOFF__=`** on stdout. See
[ADR-015 — Runtime truth restoration](./ADR-015-runtime-truth-restoration.md).

The repository **no longer** ships `providers/telegram/`, `tools/agent_telegram/`,
or `_smoke_telegram_*` entrypoints. The sections below describe the **v19.2.0**
design only for archive readers.

## Context (v19.2.0)

Operators wanted a stdlib-only adapter plus a separate control plane for
webhooks, bots, and secret rotation without bloating `runtime/`.

## Decision (historical)

1. Runtime adapter invoked Bot API `sendMessage` when base URL, token, and chat id were present; companion tools lived under `tools/agent_telegram/`.
2. Optional chat allowlists and webhook HMAC verification in operator scripts.
3. Release gates included Telegram-oriented smokes.

## Consequences (historical)

- Tight coupling between “skill tree” and a specific messenger complicated the
  compute/delivery boundary; ADR-015 and later refactors reversed that for the
  packaged skill.
