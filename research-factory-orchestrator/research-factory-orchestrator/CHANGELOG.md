# Changelog

## 19.4.x — bridge + compute-only boundary

- Default bridge profile `live-bridge`; relay base URL required (no baked search host).
- Removed in-tree Telegram delivery (`providers/telegram/`, `tools/agent_telegram/`)
  and optional golden diff helper; docs/schemas label legacy `telegram_messages` field.
- Outbox: missing provider adapter is `failed` with `PROVIDER-DELIVERY-ADAPTER-MISSING`,
  not silent `sent`. Feature matrix uses `external_user_visible_delivery_via_skill`.

## 19.2.1 — 2026-05-07

- Honesty hardening: canonical skill-path + runs-root guardrails with explicit
  refusal stamps (`RFO-NON-CANONICAL-SKILL-PATH`, `RFO-RUNS-ROOT-FORBIDDEN`).
- Telegram routing hardening: `chat_id` resolution `request -> argv -> env(consent) -> fail`
  and explicit `delivery_not_proven` flow without silent `stub_only` fallback.
- Verifier hardening: added lie classes for wrong skill path, wrong runs root,
  delivery stub without consent, and narrative without evidence.
- Smoke/repro wrappers: added `_smoke_v19_2_1_honesty.py` and
  `_smoke_v19_2_1_repro_baseline.py` (legacy repro scripts retired in v19-only cleanup).

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
