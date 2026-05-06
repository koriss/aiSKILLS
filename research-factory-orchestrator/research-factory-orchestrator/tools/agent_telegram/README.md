# Agent Telegram control plane (v19.2.0)

Operator-facing helpers for Telegram delivery **outside** the core RFO
runtime path. The canonical production send for packaged runs remains
`providers/telegram/telegram_delivery_adapter.py` (invoked by
`runtime/outbox_impl.py`).

## Layout

- `security.py` — chat allowlist + secret redaction helpers.
- `runner.py` — fixed `argv` subprocess runner (no shell).
- `telegram_bot.py` / `webhook_server.py` — host integration sketches (stdlib).
- `config.example.env` — required environment variables.
- `nginx/` / `systemd/` — deployment notes for TLS + service isolation.

See `docs/adr/ADR-014-telegram-operator-control-plane.md`.
