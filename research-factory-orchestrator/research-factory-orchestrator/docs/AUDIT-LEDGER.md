# Audit ledger — полная актуализация доков RFO

Компактный статус по объектам. Подробности и полный список путей: **`docs/RFO-DOC-SYNC-STATE.md`**.

Шаблон строки: `путь | тип | статус | действие | проверка`

| Путь | Тип | Статус | Действие | Проверка |
|------|-----|--------|----------|----------|
| README.md | normative | OK | Добавлена строка про semver из version.json | validate_skill |
| CHANGELOG.md | narrative | OK | Без изменений (актуален) | — |
| SKILL.md | normative | OK | Без изменений | validate_skill |
| SKILL-core.md | normative | OK | Без изменений | validate_skill |
| AGENTS.md | normative | OK | Без изменений | validate_skill |
| docs/v19/README.md | normative | устарел→исправлен | Переписан ввод (не design-only freeze) | validate_skill |
| docs/PROFILE_DEFAULTS.md | normative | OK | Сверка с run-profiles.json / скриптами — совпадает | — |
| failure-corpus/index.json | normative | drift→исправлен | version 19.0.1→19.2.1 под runtime | validate_skill |
| docs/v19/ci-vs-runtime.md | normative | OK | Путь к схеме transcript → schemas/core | validate_skill |
| docs/v19/run-core-validators-spec.md | normative | OK | python3 -S; профили как реализовано | validate_skill |
| docs/v19/validators-core.md | normative | OK | Ссылка на validate_skill.py required_scripts | validate_skill |
| docs/v19/schemas-core.md | normative | OK | Примечание про schemas/core копии | validate_skill |
| docs/v19/failure-fixtures.md | normative | OK | Правило версий индекса vs runtime | validate_skill |
| docs/adr/ADR-001-v19-pragmatic-rigor.md | normative | OK | Status: implemented | — |
| docs/qa/assertion-command-matrix.md | normative | OK | Строки bridge/packet/bundle/smoke/manual | validate_skill |
| docs/qa/RFO-CANONICAL-WORK-ROOTS.md | normative | new | Карта git vs пакета | human |
| docs/qa/RFO-VERSION-QUALITY-MATRIX.md | narrative | new | ZIP инвентарь vs канон | human |
| docs/qa/RFO-FULL-RESEARCH-PLAYBOOK.md | normative | new | GH1–GH3 relay/troubleshooting | validate_skill peer |
| docs/qa/RFO-MERGE-ANTI-REGRESSION.md | normative | new | §0A merge чеклист | human |
| docs/qa/NEUTRALITY-SCAN.md | normative | new | rg gate + allowed residuals | human |
| docs/adr/ADR-019-host-handoff-stdout-scanning.md | normative | new | upstream parse guidance | human |
| kb/README.md | narrative | new | Маркер non-canonical | — |
| prompts/README.md | narrative | new | Маркер non-canonical | — |
| references/README.md | narrative | new | Маркер non-canonical | — |
| examples/README.md | narrative | new | Маркер illustrative | — |
| contracts/golden-reference.md | narrative | OK | Ревью без правок | — |
| contracts/fixture-hygiene.md | normative | OK | Ревью без правок | validate_v19_fixture_suite |

## Матрица утверждение → проверка

Дублируется в **`docs/qa/assertion-command-matrix.md`** (канон для копирования в релизные чеклисты).
