# RFO — документ состояния синхронизации доков и проверок

Журнал ведётся **на границе объектов**: после завершения работы над файлом/блоком — запись здесь и в `docs/AUDIT-LEDGER.md`, затем переход к следующему объекту.

## Шапка сессии

| Поле | Значение |
|------|-----------|
| Дата (UTC) | 2026-05-10 |
| Git branch | `cleanup/v19-only-version-purge` |
| Начальный commit | `76b59ce` |
| Checkpoint commit (doc-sync bundle) | `71b722e` |
| `skill_version` (канон) | `19.3.1` из `runtime/version.json` |
| `failure_corpus_index_version` (канон) | `19.2.1` из `runtime/version.json` |

## Master list — затронутые пути

Полный перечень файлов, изменённых или созданных в ходе этой синхронизации:

- `docs/RFO-DOC-SYNC-STATE.md` (этот файл)
- `docs/AUDIT-LEDGER.md`
- `README.md`
- `docs/v19/README.md`
- `failure-corpus/index.json`
- `docs/v19/ci-vs-runtime.md`
- `docs/v19/run-core-validators-spec.md`
- `docs/v19/validators-core.md`
- `docs/v19/schemas-core.md`
- `docs/v19/failure-fixtures.md`
- `docs/adr/ADR-001-v19-pragmatic-rigor.md`
- `docs/qa/assertion-command-matrix.md`
- `docs/qa/RFO-DEEP-ANALYSIS-2026-05.md`
- `docs/qa/RFO-REMEDIATION-ROADMAP.md`
- `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`
- `docs/qa/RFO-TRUTH-CONTRACTS-ALIGNMENT.md`
- `kb/README.md`
- `prompts/README.md`
- `references/README.md`
- `examples/README.md`

## Журнал по волнам / объектам

### Wave A — входные точки

- **README.md** — добавлена отсылка к `runtime/version.json` и CHANGELOG как к источнику semver.
- **CHANGELOG.md** — обновлена секция 19.4.x (single dossier funnel, см. ADR-019).
- **SKILL.md / SKILL-core.md** — просмотр: версии и пути согласованы с `runtime/version.json`; правок не потребовалось.
- **AGENTS.md** — дефолтный профиль моста: **`dossier`** (relay).
- **docs/v19/README.md** — переписан ввод: убрано ложное «design-only / no changes to runtime»; добавлены ссылки на текущую линию и ADR.
- **docs/PROFILE_DEFAULTS.md** — сверено с `contracts/run-profiles.json` (`default_profile`: **`dossier`**) и дефолтами `run_rfo_with_web_search.py` / `run_core_validators.py` (ADR-019).

### Wave B — validators / CI–runtime

- **docs/v19/ci-vs-runtime.md** — путь к схеме transcript обновлён на актуальный `schemas/core/validation-transcript.schema.json`.
- **docs/v19/run-core-validators-spec.md** — CLI приведён к `python3 -S`; профили описаны как реализованные (`validation-profiles/` в корне репо).
- **docs/v19/validators-core.md** — добавлена ссылка на инвентарь обязательных скриптов в `scripts/validate_skill.py`.

### Wave C — схемы

- **docs/v19/schemas-core.md** — уточнено наличие замороженных копий в `schemas/core/` для рантайм-контура.
- **contracts/golden-reference.md** — ревью: текущая практика без telegram-golden; согласовано с ADR по delivery truth.
- **contracts/fixture-hygiene.md** — ревью: требования к `tests/fixtures/v19/*` согласованы с скриптами suite.

### Wave D — failure corpus

- **failure-corpus/index.json** — поле `version` выровнено к `19.2.1` для согласования с `failure_corpus_index_version` в `runtime/version.json`.
- **docs/v19/failure-fixtures.md** — добавлено правило согласования версий индекса и runtime.

### Wave E — ADR

- **docs/adr/ADR-001-v19-pragmatic-rigor.md** — статус обновлён: решение принято и реализовано в линии v19.3.x.

### Wave F–G — references / kb / prompts

- Добавлены **`kb/README.md`**, **`prompts/README.md`**, **`references/README.md`**, **`examples/README.md`** с явной маркировкой non-canonical / illustrative относительно `SKILL.md`, `runtime/`, `contracts/`, `scripts/validate_skill.py`.

### Matrix

- **`docs/qa/assertion-command-matrix.md`** — таблица «утверждение → команда проверки» для закрытия матрицы из плана.

### Wave H — deep remediation (2026-05 incident documentation)

- **`docs/qa/RFO-DEEP-ANALYSIS-2026-05.md`** — единый разбор симптомов (lease / mvr / delivery boundary) и классификация failure modes.
- **`docs/qa/RFO-REMEDIATION-ROADMAP.md`** — дорожная карта workstream’ов (очередь, профили, delivery UX, bridge, контракты).
- **`docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`** — безопасный triage `queue/worker.lease` и recovery.
- **`docs/qa/RFO-TRUTH-CONTRACTS-ALIGNMENT.md`** — выравнивание `runtime-status`, manifest, feature-truth, handoff.
- **`docs/qa/RFO-REMAINING-PLAN.md`** — секция D: статус документов deep remediation.
- **`docs/qa/assertion-command-matrix.md`** — строки верификации на новые документы.

## Реестр команд (smoke)

| Команда | Исход |
|---------|--------|
| `python3 -S scripts/validate_skill.py` | pass (после удаления артефактных `tests/__pycache__` на рабочей копии); повторно **pass** после коммита `71b722e` |
| `python3 -S scripts/rfo_runtime_core.py failure` | отчёт покрытия F-классов (может быть `status: fail` при неполном покрытии — известное состояние индекса, не регрессия док-синка) |

## Если пиздец (откат)

1. Критичные файлы: `SKILL.md`, `runtime/version.json`, `failure-corpus/index.json`, корневые контракты в `contracts/`.
2. Откат к известному хорошему коммиту: **`71b722e`** (зафиксированный doc-sync) или **`76b59ce`** (начало этой синхронизации до бандла).
3. Повторная проверка: `python3 -S scripts/validate_skill.py` из корня пакета скилла.

## Wave — QA quality / playbooks (2026-05-10)

- Добавлены `docs/qa/RFO-CANONICAL-WORK-ROOTS.md`, `RFO-VERSION-QUALITY-MATRIX.md`, `RFO-FULL-RESEARCH-PLAYBOOK.md`, `RFO-MERGE-ANTI-REGRESSION.md`; расширен `docs/qa/assertion-command-matrix.md`.
- Honesty verifier canonical: `scripts/verify_skill_run_claims.py` + wrapper `verify_openclaw_run.py`; `validator_id` в JSON → **verify_skill_run_claims**.
- Handoff downstream index: `agent-handoff/bundle-manifest.json`; роли промптов `prompts/roles/*.md`; ADR **`docs/adr/ADR-019-host-handoff-stdout-scanning.md`** (upstream parse).
- Neutrality gate: `docs/qa/NEUTRALITY-SCAN.md` with explicit `rg` command and allowed residuals.
- `kb/propaganda-io/` на канонической копии: манифест + `io-kb-unified/`, без восстановления из ZIP `_tmp/rfo`.

### Дополнение master list затронутых путей

- `CHANGELOG.md`, `SKILL.md`, `runtime/report_html.py`, `runtime/chat_md.py`, `runtime/artifact_execute_impl.py`, `scripts/validate_skill.py`, `scripts/_rfo_path_guard.py`, `scripts/verify_skill_run_claims.py`, `scripts/verify_openclaw_run.py`
- `prompts/README.md`, `prompts/roles/*.md`, `contracts/golden-reference.md`, `docs/AUDIT-LEDGER.md`, `docs/adr/ADR-019-host-handoff-stdout-scanning.md`, `docs/qa/NEUTRALITY-SCAN.md`
