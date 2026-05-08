# Phase 2 — Hardcode hunt (text + AST)

**Скоуп**: весь `SKILL_DIR=research-factory-orchestrator/`, исключения: `.git/`, `.venv/`, `.tmp-exec-runs/`, `__pycache__/`, `*.pyc`.

**Артефакты сырой охоты**: `03-hardcode-hunt/`
- `01-search-engines.txt` — 68 строк (search backends)
- `02-delivery-channels.txt` — 29 строк (telegram/discord/slack/sendMessage/chat_id)
- `03-http-domains-all.txt` — 1874 строки (все http(s) URLs)
- `04-backend-envs.txt` — 20 строк (`TELEGRAM_*`, `BRAVE_*`, `SEARXNG_*` и т.п.)
- `05-http-clients-runtime.txt` — 1 строка (только `runtime/`)
- `06-ast-runtime.json` — AST-скан runtime/: 9 файлов с findings, 2 url-строки, 23 env lookup, 1 network-import.
- `07-bucketed-summary.txt` — те же сырые строки, но разложенные по бакетам.

## 2.1 — text rg

### RUNTIME (severity: HIGH — нарушает agent-native, если не обёрнуто)

| Файл | Строка | Значение | Категория |
|------|--------|----------|-----------|
| `runtime/cli.py` | 29 | комментарий о `chat_id` MUST come from incoming update | Telegram-specific term |
| `runtime/adapter_impl.py` | 27 | `"chat_id": _opt(getattr(a, "chat_id", ""))` | Telegram-specific field |
| `runtime/artifact_execute_impl.py` | 24 | `"chat_id": None` | Telegram-specific field |
| `runtime/compatibility-matrix.json` | 15 | `upgrade_notes` упоминает `TELEGRAM_API_BASE`, `Telegram real sendMessage` | історичні нотатки в matrix-файлі |
| `runtime/worker_impl.py` (AST) | 85 | `os.environ.get("RFO_ALLOW_ENV_CHAT_ID")` | guard-flag, name leaks Telegram |

**Вывод RUNTIME**: рантайм формально содержит Telegram-смыслящие термины (`chat_id`, `TELEGRAM_API_BASE` в matrix-нотах, `RFO_ALLOW_ENV_CHAT_ID`). Это **не сетевой клиент**, а имена полей delivery-плана и компат-нотки. Архитектурно это либо:
- (а) часть delivery-vocabulary, который оставили как «least-common-denominator» для adapter contract → тогда нужно переименовать в нейтральное (`recipient_id` / `target_id` / `delivery.recipient`),
- (б) фактический Telegram-хардкод → тогда нужен отдельный план refactor.

В любом из вариантов `runtime/compatibility-matrix.json:15` (исторические notes в production-файле) и `runtime/worker_impl.py:85` (`RFO_ALLOW_ENV_CHAT_ID`) — однозначные finding'и для документирования.

### PROVIDERS (severity: HIGH, runtime path)
- `providers/cli/` — оставлены после rsync.
- `providers/webhook/` — оставлены после rsync.
- `providers/telegram/` — **удалены** в Pre-Phase rsync (соответствует agent-native цели).
- В файле `02-delivery-channels.txt` для `providers/` нет ни одного хита.

### CONTRACTS / POLICIES / VALIDATION-PROFILES / PLAYBOOKS (severity: HIGH, ratchet)
- 0 хитов по всем категориям (search-engines, delivery-channels, backend-envs, http-clients).
- `provider-contract.json`, `provider-capabilities.json`, `delivery-contract.json`, `interface-adapter-contract.json`, `run-profiles.json`, `source-acquisition-reliability-contract.json` — **чистые** по rg-маркерам (детальный аудит — Phase 3).

### SCRIPTS (severity: MEDIUM, не входит в hot path runtime, но нарушает agent-native по интенту скилла)

**Search backends (массивный хардкод):**
- `scripts/run_rfo_with_web_search.py` — 13 хитов, явный SearXNG/Wikipedia bridge.
  - `:51` `_SEARCH_ENDPOINT = os.environ.get("RFO_SEARXNG_URL", "http://searxng:8080")` — default URL зашит.
  - `:86` `https://en.wikipedia.org/w/api.php?...` — прямой call.
- `scripts/run_rfo_full_research.py` — 14 хитов, тот же SearXNG/Wikipedia/Google/Bing pipeline.
  - `:35` `_SEARXNG = os.environ.get("RFO_SEARXNG_URL", "http://searxng:8080")` — default URL зашит.
  - `:306` `"backend": "searxng"` — backend имя зашито в манифест.
  - `:343` `"SearXNG web search (Google, Bing, Wikipedia engines)"` — методология описывает конкретные backends.

**Delivery channels (Telegram-specific scripts):**
- `scripts/_smoke_v19_2_1_honesty.py`, `scripts/_smoke_v19_2_1_repro_after_fix.py` — Telegram smoke-тесты с `TELEGRAM_BOT_TOKEN`, `RFO_ALLOW_ENV_CHAT_ID`, `TELEGRAM_CHAT_ID`.
- `scripts/interface_runtime_adapter.py` — argv adapter `--chat-id`, `--api-base` defaults to `https://api.telegram.org`.
- `scripts/_rfo_path_guard.py` — example block с `TELEGRAM_API_BASE`.
- `scripts/verify_openclaw_run.py` — описание silent stub path с `chat_id`.

**Validators (legitimate ratchets, OK):**
- `scripts/validate_no_provider_hardcode_text.py:7` — regex `sendMessage|sendDocument` как **anti-pattern detector**.
- `scripts/validate_provider_specific_logic_not_in_runtime.py:15` — то же самое.

### TOOLS (severity: LOW — operator-side, не входит в runtime/scripts hot path)
- `tools/agent_telegram/` — содержит реальный Telegram bot и pre-share env. По плану (вопрос 3 из плана, default-ответ) — оставлено как operator-side. **Не нарушение** при условии, что runtime/ не импортирует из tools/.

### TEMPLATES (нет хитов)

## 2.2 — AST runtime

Сводка `06-ast-runtime.json`:

- 38 .py файлов в `runtime/` отсканировано, 9 с findings.
- **0 импортов** `requests`, `httpx`, `aiohttp`. Сетевой клиент только один: `runtime/collector.py:29 import urllib.request`.
- **2 URL-строки в коде**:
  - `runtime/collector.py:36` `"RFO/19.2.0 (+https://github.com/openclaw/research-factory-orchestrator)"` — User-Agent. **OK** (метаинформация о скилле, не backend).
  - `runtime/worker_impl.py:271` `"runtime.completed"` — это event name, не URL (false positive фильтра).
- **23 env lookup в runtime/**, имена:
  - Чистые `RFO_*`: `RFO_RUN_PROFILE`, `RFO_SEED_URLS`, `RFO_EXTERNAL_COLLECTION`, `RFO_CAP_SECRET`, `RFO_MAX_EXTERNAL_SOURCES`, `RFO_SOURCE_PACKET`, `RFO_NO_NETWORK`, `RFO_HTTP_TIMEOUT`, `RFO_FIXED_TIME`, `RFO_V19_PROFILE`, `RFO_ID_SALT`, `RFO_DETERMINISTIC_IDS`, `RFO_LEGACY_EVENT_NAMES`, `RFO_ALLOW_TMP_RUNS_ROOT`.
  - **Backend-смыслящие**: `RFO_ALLOW_ENV_CHAT_ID` (`runtime/worker_impl.py:85`) — guard для Telegram chat_id из env.

## Severity rollup (Phase 2)

| Bucket | Search engines | Delivery channels | Backend envs | HTTP clients | Severity |
|--------|---------------:|------------------:|-------------:|-------------:|---------:|
| RUNTIME | 0 | 4 | 1 (matrix notes) + 1 (worker AST) | 0 | **HIGH** |
| PROVIDERS | 0 | 0 | 0 | 0 | OK |
| CONTRACTS / POLICIES / PLAYBOOKS / VALIDATION-PROFILES | 0 | 0 | 0 | 0 | OK |
| SCRIPTS | 27 (run_rfo_*.py) | 9 (smokes/adapter/guard) | 7 | 0 | **MEDIUM** |
| TOOLS | 0 | 4 (operator agent_telegram) | 6 (operator agent_telegram) | 0 | LOW (out-of-scope) |
| TEMPLATES | 0 | 0 | 0 | 0 | OK |

## Открытые наблюдения для Phase 6 priority list

1. **runtime/ Telegram-vocab leak** — `chat_id` присутствует в трёх runtime-модулях (cli/adapter_impl/artifact_execute_impl); поле delivery-плана называется по-Telegram'ему. Архитектурный вопрос: переименовать в нейтральное имя или официально объявить `chat_id` нейтральным «recipient_id» термином в delivery-vocabulary.
2. **runtime/compatibility-matrix.json** — historical `upgrade_notes` содержат `TELEGRAM_API_BASE`. Это runtime-файл (matrix), а не doc. Кандидат на обезличивание.
3. **runtime/worker_impl.py — `RFO_ALLOW_ENV_CHAT_ID`** — env-переменная, name которой leak'ает Telegram-семантику. Кандидат на переименование в `RFO_ALLOW_ENV_RECIPIENT` или аналог.
4. **scripts/run_rfo_with_web_search.py** и **scripts/run_rfo_full_research.py** — самое яркое нарушение agent-native: целые скрипты-bridge'ы с зашитым SearXNG/Wikipedia. По смыслу плана: это **MEDIUM**, не HIGH (они вне runtime hot-path), но именно они отвечают на вопрос пользователя «где я ещё хардкожу». Кандидаты: либо вынести в `examples/`/`tools/`, либо удалить, либо перевести в строго-параметрический режим (агент должен передавать backend URL).
5. **tools/agent_telegram/** — operator-side; по plan'у оставлено. Зафиксировано как not-runtime, не считается нарушением.
6. **Валидаторы** `validate_no_provider_hardcode_text.py` и `validate_provider_specific_logic_not_in_runtime.py` корректно ловят `sendMessage|sendDocument` в коде (запускались в Phase 1 и подтвердили matrix/cli/scripts hits).
