# PLAN 19.4.1.1 (канонический релиз **19.4.3**) — накопленные правки

Внутреннее имя волны **19.4.1.1**; семвер в репозитории поднят до **19.4.3** (`runtime/version.json`, `SKILL.md`).

## Цели

1. **Citation grounding / RAF** — устранить математически невыполнимый порог для `inferred_assessment` при одном слоте `support_set` (старый `min(sc/2,1)*0.52` давал максимум **0.52** при любом числе опор).
2. **`sources.json` в `run_rfo_full_research.py`** — только поля v19-схемы; общая нормализация с мостом.
3. **Синхрон harness ↔ контракт** — `validate_citation_grounding` в цепочке `run_core_validators.py` и в `validation-profiles/dossier.json` / `search-primary.json`; опциональный пропуск при отсутствии файла, если профиль не требует grounding.
4. **Discovery** — `validate_skill_discovery_frontmatter.py` принимает `19.4.x` (и сохраняет `19.3.x`).
5. **Хост-агент / эмбеддинг** — отдельный промпт обрезки текста до embed: `prompts/host-agent-embedding-truncate.md`.

## Статус реализации (этот PR)

| Пункт | Состояние |
|-------|-----------|
| RAF + вес `inferred_assessment` | `runtime/citation_grounding.py` |
| Общий модуль источников | `runtime/source_record_v19.py` |
| Мост | `scripts/run_rfo_with_web_search.py` → импорт нормализации |
| Full research | `scripts/run_rfo_full_research.py` — чистые записи + нормализация |
| V1–V6+CG chain | `scripts/run_core_validators.py` + профили |
| Валидатор optional | `scripts/validate_citation_grounding.py` |
| Версии / CHANGELOG / run-profiles | см. коммит |

## Не в этом патче (напоминание)

- Полная оркестрация «волн» как продуктовый default — см. `docs/plans/rfo-prod-repair-plan.md` и ADR-019.
- Синхронизация всех вторичных доков с `19.4.0` в prose — по мере касания файлов; канон semver: `runtime/version.json`.
