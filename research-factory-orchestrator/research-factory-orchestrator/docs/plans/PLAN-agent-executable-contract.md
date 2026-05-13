---
name: RFO agent-executable contract
overview: >
  Зафиксировать deterministic RFO contract, исполнимый обычным IDE/CLI-агентом
  с доступом только к shell/python/read/write/search внутри каталога навыка.
  Production research требует явные внешние входы и fail-fast при их отсутствии.
  In-repo тесты используют только явно маркированный fixture/offline режим и не
  могут выдаваться за настоящий web research. Агент обязан различать production
  run, fixture validation и blocked external dependency.
todos:
  - id: contract-schema-effective-config
    content: >
      Расширить effective-config / preflight JSON (или смежный контракт) полем
      run_execution_mode: canonical_production | test_fixture | blocked_external_dependency;
      validators и доки ссылаются на него; production никогда не помечается fixture без явного argv/env.
    status: pending
  - id: docs-skill-runtime-paths
    content: >
      SKILL.md + SKILL-core.md + docs/runtime-paths.md: одна каноническая секция
      «Agent-executable contract» со ссылкой на этот план; убрать любые формулировки
      «сделай SearXNG / docker» как цель продукта.
    status: pending
  - id: agent-forbidden-actions
    content: >
      Зафиксировать в контракте/валидаторах: агенту запрещено подменять RFO web_search,
      выдавать fixture за production, скрывать non-zero exit, утверждать «RFO отработал»
      без canonical run + дисковых гейтов.
    status: pending
isProject: true
---

# План: Agent-executable contract (RFO)

Этот документ — **отдельный** продуктово-архитектурный план. Он **не** заменяет
`docs/plans/rfo-prod-repair-plan.md` и не смешивается с починкой citation/профилей:
там своя очередь задач. **Расширенный in-repo контракт (argv runs-root, fixture mode, doc-grep):** `docs/plans/PLAN-rfo-agent-executable-single-behavior.md`.

## Зачем отдельный план

Цель проекта формулировать **не** как «сделать так, чтобы у агента был SearXNG», а так:

RFO skill должен быть **исполним агентом** в любой среде, где у него есть только стандартные инструменты: **shell**, **python**, **read/write**, **search по репозиторию**.

Если настоящего web relay нет, агент **не должен врать**, что выполнил full web run. Он обязан выполнить **preflight**, определить недостающий внешний input, зафиксировать это в **effective-config / diagnostics** и перейти в **явно разрешённый** режим:

- **fail-fast** для canonical production;
- **fixture/offline** только для тестов навыка;
- или **`blocked: missing relay`** для реального запроса без входов.

Ключевая формулировка приоритетов:

> Не «сделать так, чтобы работало у меня». А «сделать так, чтобы любой агент мог честно выполнить максимум возможного на своих инструментах и **не смешивал** fixture/test/preflight с production RFO».

Это правильнее, чем зашивать в навык «локальный relay, который магически заменяет SearXNG» — иначе снова появится скрытый fallback под другим именем.

## Agent-executable contract (полный текст)

Навык должен быть выполним **обычным IDE/CLI-агентом** без предположений о наличии OpenClaw, Docker, SearXNG, gateway или внешнего relay.

Агенту **гарантированы** только:

- чтение файлов;
- поиск по репозиторию;
- shell;
- python3;
- возможность править файлы внутри каталога навыка;
- запуск unit tests / validators.

Навык **не должен требовать** от агента:

- поднять docker compose;
- править `/opt/openclaw/**` (или любой чужой деплой);
- иметь DNS alias `searxng`;
- иметь доступ к production gateway;
- иметь настоящий web relay **для самопроверки навыка** (relay нужен invoker’у для canonical production — см. режимы ниже).

Контракт делится на **три режима**:

### 1. Canonical production run

Используется, когда invoker **явно** передал все внешние входы:

- `--runs-root` (или workspace → `rfo-runs` по `runtime/config_resolution.py`);
- `--web-search-json-api-base` / `RFO_WEB_SEARCH_JSON_API_BASE`;
- task / profile.

Если relay отсутствует или недоступен:

- exit **non-zero**;
- понятная ошибка;
- **no** fake research;
- **no** fallback на fixture;
- **no** synthetic answer.

### 2. In-repo validation / CI / IDE-agent run

Используется для проверки навыка агентом **внутри репозитория**.

Разрешено:

- локальный **fixture relay**;
- статические **fixture sources**;
- preflight;
- validators;
- post-run answer contract tests.

Обязательно:

- явно маркировать режим как **`test_fixture`** (или эквивалент в machine-readable поле);
- писать это в **effective-config** (или соседний артефакт, согласованный со схемой);
- **не** называть такой прогон production / full web run.

### 3. Blocked external dependency

Если пользователь просит **реальный** research, но у агента нет relay:

Агент обязан ответить:

- RFO canonical run **blocked**;
- missing external dependency: `web_search_json_api_base` / relay unavailable;
- какие команды / preflight прошли;
- какой input нужен от invoker / gateway.

Агенту **запрещено**:

- подменять RFO обычным `web_search` (или любым «рассказом без run_dir»);
- выдавать fixture run как реальный;
- скрывать падение;
- писать «RFO отработал», если canonical run не прошёл.

## Связь с кодом и документацией

- Реализация режимов и маркировки — через **preflight**, **`effective-config.json`**, схему
  `contracts/rfo-effective-config-v1.schema.json` (расширения — отдельным PR).
- Операторский путь без «магии»: `docs/runtime-paths.md`, `SKILL-core.md`.
- Этот файл — **источник смысла** для формулировок в overview и в onboarding агентов;
  конкретные PR по todo выше не обязаны менять всё сразу.

## Вне scope этого плана

- Конкретный выбор search engines у SearXNG (это политика **relay/инстанса**, не цель навыка).
- Починка citation / wave-plan / standalone legacy — см. `rfo-prod-repair-plan.md`.
