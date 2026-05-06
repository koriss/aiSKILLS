# Changelog

## 19.2.0 — 2026-05-02

- Runtime truth restoration: v19 artifact emission, collection/coverage decoupling,
  work-unit completion guards, integration smokes (`_smoke_v19_2_*`).
- Telegram: real `sendMessage` path + operator `tools/agent_telegram/` + mock API
  smoke (`_smoke_telegram_real_send`).
- Release: POSIX subprocess `killpg` hardening in `validate_release.py`,
  `failure-corpus/index-v19.json` meta registry bump, `verify_openclaw_run.py`.

## 19.1.0 — 2026-04 (backfill)

- Multi-agent advisory stack + deterministic replay smokes (ADR-012/013).
- Release zip triad + clean-install smoke + coverage meta gate.

## 1.0.0
- Initial release: `research-factory-orchestrator` with default `AUTO_COMPILE_AND_EXECUTE`, global/item FSM, internal compiler + executor protocols, templates, JSON schemas, playbooks, init/validate scripts, examples, and regression tests.
