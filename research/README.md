# research

Production-grade skill для OpenClaw: расследования и проверка тезисов с **orchestration** поверх **deep-investigation-agent**.

**Чат (v1.1+):** по умолчанию минимум шума — опционально одно короткое ack, при задержке одно фиксированное сообщение, затем **HTML → проверка → отправка файла → один финальный текст** (`templates/final-chat-response.txt`). Подробности: `references/chat-policy.md`.

## Быстрый старт

1. Скопируй каталог `research/` в workspace агента, например `/home/node/.openclaw/workspace/skills/research/`.
2. Убедись, что доступен skill `deep-investigation-agent` как аналитическое ядро.
3. Проверка структуры:

```bash
python3 scripts/check_skill.py .
```

4. Валидация JSON-артефактов (нужен `jsonschema`):

```bash
pip install jsonschema
python3 scripts/validate_artifacts.py path/to/final-report.json path/to/subagent-results.json
```

5. Сборка HTML из `final-report.json`:

```bash
python3 scripts/assemble_report.py examples/final-report.json reports/out.html
```

## Состав

| Путь | Назначение |
|------|------------|
| `SKILL.md` | Основной контракт агента |
| `references/` | Orchestration, retry, Telegram, логи, формат отчёта, **chat-policy** |
| `schemas/` | JSON Schema для артефактов |
| `templates/` | HTML, финальный ответ в чате, плотная Telegram-выжимка |
| `scripts/` | Проверка skill, валидация, сборка HTML, хелперы критики |
| `examples/` | Примеры запросов, JSON, сводка, артефакт subagent, **chat-policy-scenarios** |

## Артефакты прогона

- `final-report.json` — ядро + `investigation_report` + `orchestration_meta` + `verify_claims`
- `subagent-results.json`
- `execution-log.json`
- `quality-review.json`
- HTML по шаблону `templates/report.html`
- Файлы subagent-ов в `reports/subN-<slug>-DATE.txt`

Пути по умолчанию: `/home/node/.openclaw/workspace/reports/` (см. `SKILL.md`).
