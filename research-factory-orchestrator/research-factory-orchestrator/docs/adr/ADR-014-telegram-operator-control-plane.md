# ADR-014 — Telegram operator control plane (v19.2.0)

## Status

Superseded for **delivery posture** by [ADR-015 — Compute vs delivery split](./ADR-015-compute-vs-delivery-split.md) (v19.3): user-visible Telegram delivery and proofing move to **OpenClaw gateway**; the skill stays compute-only with a stdout marker + `result-manifest.json`.

Historically accepted — implemented in v19.2.0 (`tools/agent_telegram/`, `_smoke_telegram_*`) before the split.

## Context

Packaged runs must keep a **stdlib-only** delivery adapter under `providers/telegram/`
for `runtime/outbox_impl.py`. Host operators also need a **separate** control plane
for webhooks, long-poll bots, and secret rotation without growing runtime core.

## Decision

1. **Split responsibility** — runtime adapter = minimal `sendMessage` when
   `TELEGRAM_API_BASE` + token + chat id are present; operator tools live under
   `tools/agent_telegram/`.
2. **Chat allowlist** — optional `TELEGRAM_ALLOWED_CHAT_IDS` enforced in
   `tools/agent_telegram/security.py` for operator entrypoints.
3. **Secret redaction** — `security.redact_secrets` scrubs tokens before logging.
4. **Fixed argv** — `tools/agent_telegram/runner.py` documents subprocess policy
   (no shell, explicit argv).
5. **Webhook HMAC** — `webhook_server.py` verifies `X-Telegram-Bot-Api-Secret-Token`
   when `TELEGRAM_WEBHOOK_SECRET` is set (host should still terminate TLS in nginx).

## Consequences

- Two smokes are mandatory in `REQUIRED_GATES`: interface contract + mock Bot API
  trace (`_smoke_telegram_agent_interface`, `_smoke_telegram_real_send`).
