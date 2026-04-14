# aiSKILLS

Каталог навыков (skills) для агентов и ClawHub: каждый скилл — отдельная папка с `SKILL.md` и при необходимости ресурсами в `resources/`.

## Скилы


| Скил                            | Путь                                                           | Кратко                                                                                                                                           | Когда использовать                                                                                                           |
| ------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **ClawHub Publication Auditor** | `[clawhub-publication-auditor/](clawhub-publication-auditor/)` | Глубокий аудит готовности к публикации в ClawHub: код, упаковка, метаданные, контракты, примеры, доки, портируемость, безопасность, диагностика. | Перед публикацией skill или package в ClawHub, при release readiness, при проверке гигиены артефакта и риска отказа реестра. |
| **Deep Investigation Agent**    | `[deep-investigation-agent/](deep-investigation-agent/)`       | Исследование сложных тем: веб-поиск, проверка источников, конкурирующие гипотезы, карта доказательств, отчёты для решений.                        | Спорные/быстро меняющиеся темы, геополитика, экономика, безопасность, здоровье, корпоративный анализ, когда важна верификация. |


### ClawHub Publication Auditor — детали

- **Имя в метаданных:** `clawhub-publication-auditor`
- **Риск (из skill):** `medium`
- **Полное описание:** см. frontmatter в `[clawhub-publication-auditor/SKILL.md](clawhub-publication-auditor/SKILL.md)`.
- **Ресурсы:** чеклисты и шаблоны в `[clawhub-publication-auditor/resources/](clawhub-publication-auditor/resources/)` (`publication-checklist.md`, `findings-template.md`, `manifest-review.md`, `skill-vs-package-decision.md`, `release-blockers.md`).

### Deep Investigation Agent — детали

- **Имя в метаданных:** `deep-investigation-agent`
- **Лицензия (из skill):** `CC0-1.0`
- **Полное описание:** см. frontmatter и контракт в `[deep-investigation-agent/SKILL.md](deep-investigation-agent/SKILL.md)`.
- **Состав:** `references/` (методология, источники, гипотезы, контракт вывода), `schemas/investigation_report.schema.json`, `scripts/` (`check_skill.py`, `validate_report.py`), `examples/` (пример запроса и отчётов).
- **Запуск валидаторов:** см. раздел Validation в `[deep-investigation-agent/README.md](deep-investigation-agent/README.md)`.

## Как добавить новый скил

1. Создай каталог `имя-скила/` в корне репозитория.
2. Положи туда `SKILL.md` с frontmatter (`name`, `description`, при необходимости `source`, `risk`).
3. Добавь строку в таблицу **Скилы** в этом README.
4. Закоммить и отправь изменения.

## Лицензия

По умолчанию содержимое репозитория распространяется на условиях, указанных в `LICENSE` (добавь файл при необходимости).