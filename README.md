# aiSKILLS

Каталог навыков (skills) для агентов и ClawHub: каждый скилл — отдельная папка с `SKILL.md` и при необходимости ресурсами в `resources/`.

## Скилы

| Скил | Путь | Кратко | Когда использовать |
|------|------|--------|-------------------|
| **ClawHub Publication Auditor** | [`clawhub-publication-auditor/`](clawhub-publication-auditor/) | Глубокий аудит готовности к публикации в ClawHub: код, упаковка, метаданные, контракты, примеры, доки, портируемость, безопасность, диагностика. | Перед публикацией skill или package в ClawHub, при release readiness, при проверке гигиены артефакта и риска отказа реестра. |

### ClawHub Publication Auditor — детали

- **Имя в метаданных:** `clawhub-publication-auditor`
- **Риск (из skill):** `medium`
- **Полное описание:** см. frontmatter в [`clawhub-publication-auditor/SKILL.md`](clawhub-publication-auditor/SKILL.md).
- **Ресурсы:** чеклисты и шаблоны в [`clawhub-publication-auditor/resources/`](clawhub-publication-auditor/resources/) (`publication-checklist.md`, `findings-template.md`, `manifest-review.md`, `skill-vs-package-decision.md`, `release-blockers.md`).

## Как добавить новый скил

1. Создай каталог `имя-скила/` в корне репозитория.
2. Положи туда `SKILL.md` с frontmatter (`name`, `description`, при необходимости `source`, `risk`).
3. Добавь строку в таблицу **Скилы** в этом README.
4. Закоммить и отправь изменения.

## Лицензия

По умолчанию содержимое репозитория распространяется на условиях, указанных в `LICENSE` (добавь файл при необходимости).
