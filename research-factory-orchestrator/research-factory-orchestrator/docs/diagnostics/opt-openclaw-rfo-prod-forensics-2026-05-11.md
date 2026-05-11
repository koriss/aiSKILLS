# RFO на opt-openclaw: разбор прода (2026-05-11)

Контекст: сессия в пользовательском чате хоста (команда `/research_factory_orchestrator`, субагент, затем «прямой» запуск). Ниже — **факты с диска** хоста по workspace **`/opt/openclaw/data/workspace`** плюс сопоставление с тем, что видно в переписке.

## Где смотреть (не «логи gateway в markdown», а артефакты рана)

| Что | Путь на хосте |
|-----|----------------|
| Индекс прогонов | `/opt/openclaw/data/workspace/rfo-runs/index/runs-index.jsonl` |
| Прогон «генетика балкан» (основной для разбора) | `/opt/openclaw/data/workspace/rfo-runs/runs/genetika_balkanskih_narodov_istoricheskie_migracii_etnic_20260511T010605/` |
| Ранний прогон той же темы | `.../genetika_balkanskih_narodov_istoricheskie_migracii_etnic_20260511T010458/` |
| Прогон «игра былина» | `/opt/openclaw/data/workspace/rfo-runs/runs/igra_bylina_issledovanie_russkih_narodnyh_igr_bylikov_ih_20260511T150726/` |
| Gateway (контейнер) | `docker logs openclaw-openclaw-gateway-1` — в выборке попадали **фрагменты текста ответов бота** (диагностика по смыслу ограничена; для RFO надёжнее **JSON в run-dir**). |

В индексе для обоих прогонов «генетика» указаны **`provider`: `cli`**, **`interface`: `cli`** — то есть зафиксированный на диске успешный пайплайн с артефактами соответствует **запуску через CLI-скрипт**, а не обязательно нативному обработчику команды в слое хоста с `minimax` из чата. Это согласуется с **`stub_delivered`** в манифесте доставки.

## `genetika_*_20260511T010605` — что реально записано в гейтах

Файлы: `final-answer-gate.json`, `delivery-manifest.json`, `outbox-finalization.json`, `runtime-status.json`.

Итог **`passed`: false**, **`status`: fail**.

Ключевые провалы (одинаковая картина в manifest и gate):

1. **`citation_grounding_gate`**: `status: fail`, **`validator_result_present`: false** — гейт не видит валидный артефакт результата валидатора (нужно отдельно искать в коде, **какой именно файл** ожидается и кто его должен записать в DAG).
2. **`external_delivery_gate` / `final_user_claim_gate`**: **`stub_only`**, не pass — для профиля **`cli`** в `delivery-manifest.json` явно: **`stub_delivery`: true**, **`real_external_delivery`: false**, **`publish_allowed`: false**, **`publish_reason`: `stub_only_no_external`**. Это **не дефект канала доставки**, а **контракт доставки для CLI-рана**: внешняя доставка в канал не доказывается.
3. **`wave_graph_gate`**, **`self_audit_gate`**, **`package_gate`**: в `final-answer-gate.json` отмечены как **`passed`: false** при `status: pass` у части — трактовать как «не закрыты критерии полного PASS пакета», а не как «ран упал на старте».

`outbox-finalization.json`: **`citation_grounding_passed`: false**, **`stub_only`: true**, **`finalized_at`**: `2026-05-11T15:07:27Z` (позже первичного сбора — вероятна догоняющая финализация/обновление гейтов).

`runtime-status.json`: **`state`: `stub_delivered`**, **`version`: `19.3-search-primary`**.

## Волны сбора (реле) по `graph/wave-events.jsonl`

Для `RUN-f04332678121`:

- W0: JSON relay search — **9 results**
- W1: Wikipedia full-text — **0 pages**
- W2: Web content fetch — **9 pages**
- W3: Claim extraction — **9 claims**

Это объясняет «смешанное качество источников» из переписки: часть веток дала ноль страниц Wikipedia при непустом relay/fetch.

## Прогон «игра былина» (`RUN-2bc1c96f6c76`)

`final-answer-gate.json`: **та же схема** — `citation_grounding_gate` с **`validator_result_present`: false**, доставка **`stub_only`**, общий **`passed`: false`. То есть проблема **не уникальна для темы генетики**, а системная для этого режима/версии пайплайна на проде.

## Сопоставление с перепиской (без выдумывания)

| Сообщение в чате | Подтверждение на диске |
|------------------|-------------------------|
| Валидация не прошла, citation grounding | Да: `citation_grounding_gate.fail`, `validator_result_present: false`. |
| Доставка в канал / proof | Для зафиксированного CLI-рана: `stub_only`, `publish_allowed: false` — ожидаемо для `provider: cli`. Нативная v19.3-доставка через gateway — **отдельная** цепочка; в этом файле она не отражена, если ран не шёл через неё. |
| Субагент вернул HTML вместо RFO | Артефактами run-dir **не доказывается** (это поведение агента OpenClaw, не JSON в `rfo-runs`). В SKILL/доках уже есть предупреждение не маршрутизировать slash на «голого» субагента. |
| Патч `ensure_pkg_required_paths` перед `build_package` | В **каноническом** git-пакете на момент проверки вызов из `worker_impl` **не найден** (grep только `pkg_required_scaffold` + тесты). Если патч делался **только в деплое** под `/opt/openclaw/skills/...`, его нужно **влить в репозиторий** и зафиксировать коммитом, иначе расхождение прод vs git останется. |

## Рекомендованные следующие шаги (в репозитории)

1. **Citation grounding**: найти в `scripts/` / `runtime/` условие `validator_result_present` и цепочку, которая должна записать ожидаемый JSON; воспроизвести локально на копии run-dir с прода.
2. **Развести сценарии**: документировать явно два пути — **нативный handler хоста + gateway delivery** vs **`run_rfo_full_research.py` / CLI** (`stub_delivered`), чтобы не смешивать ожидания «валидатор + подтверждаемая доставка в канал».
3. **Синхронизация с прод-скиллом**: если в `/opt/openclaw/skills/research-factory-orchestrator/` есть правки, сделать `diff` с `/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/` и перенести в git.

## Команды для повторной выборки

```bash
# индекс
tail -5 /opt/openclaw/data/workspace/rfo-runs/index/runs-index.jsonl | jq .

# гейты конкретного рана
jq . /opt/openclaw/data/workspace/rfo-runs/runs/genetika_balkanskih_narodov_istoricheskie_migracii_etnic_20260511T010605/final-answer-gate.json

# волны
cat /opt/openclaw/data/workspace/rfo-runs/runs/genetika_balkanskih_narodov_istoricheskie_migracii_etnic_20260511T010605/graph/wave-events.jsonl
```
