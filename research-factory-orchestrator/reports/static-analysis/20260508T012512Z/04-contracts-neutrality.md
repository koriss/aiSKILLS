# Phase 3 — Contract / policy / playbook / validation-profile neutrality

Цель: контракты и политики должны описывать роли (provider, channel, interface, backend), а не имена конкретных бэкендов.

Маркеры (case-insensitive): searxng, searx, google.com/search, bing.com, duckduckgo.com, brave.com, api.bing, serpapi, wikipedia.org, en.wikipedia, telegram, discord, slack, sendMessage, sendDocument, chat_id, bot_token, TELEGRAM_*, DISCORD_*, SLACK_*, BRAVE_*, SEARXNG_*, SERPAPI_*, GOOGLE_API_KEY, BING_API_KEY.

Артефакты сырые: 04-contracts-neutrality/{contracts,policies,playbooks,validation-profiles,schemas}.txt + doc-only/.

## Свод по бакетам

| Bucket | Hits | Severity | Комментарий |
|--------|-----:|----------|-------------|
| contracts/*.json | 4 | HIGH | delivery-contract.json, provider-capabilities.json, interface-adapter-contract.json явно перечисляют "telegram" |
| contracts/golden-reference.md | 5 | MEDIUM | doc, но в contracts/; ссылается на contracts/telegram-golden/ |
| contracts/handoffs/ | 0 | OK | clean |
| contracts/legacy/ | 0 | OK | clean |
| policies/*.json | 0 | OK | 4 файла clean |
| playbooks/*.md | 0 | OK | 10 файлов clean |
| validation-profiles/*.json | 0 | OK | 4 профиля clean |
| schemas/*.schema.json | 0 | OK | все JSON Schemas нейтральные |

## Конкретные нарушения (HIGH, runtime contracts)

### contracts/delivery-contract.json:7
Файл содержит явный backend-named ключ "telegram" с правилами форматирования (plain_text_only, no_tables, no_local_paths, no_raw_sensitive_contacts). Должно быть нейтральное "chat_text" или "plain_chat_profile", либо вынесено в отдельный delivery-formatting-profiles.json с ролью "chat_plain_text".

### contracts/provider-capabilities.json:12
"telegram" стоит в одном ряду с ролями cli/webhook/direct_runtime. По смыслу cli, webhook, direct_runtime — это транспорт-роли, а telegram — конкретный backend. Должно быть либо "chat_external" (роль), либо вынести Telegram в providers/telegram/capabilities.json (ratchet-аdapter), а контракт держать только с ролями.

### contracts/interface-adapter-contract.json:5,10
generic_chat, cli, web, webhook — нейтральные роли; "telegram" — конкретный backend, который сидит и в supported_interfaces, и в supported_providers. Аналогичная проблема.

### contracts/golden-reference.md
Ссылается на contracts/telegram-golden/ директорию (физически отсутствует) и на --provider telegram --interface telegram команду. Doc-only, но в области контрактов, не в docs/.

## doc-only бакет (фиксируется, не блокирует)

| Файл / папка | Hits | Категория |
|--------------|-----:|-----------|
| SKILL.md | 32 | 33 упоминания Telegram + 1 Slack + 1 Discord |
| SKILL-core.md | 1 | 1 telegram |
| AGENTS.md | 6 | TELEGRAM_API_BASE / api.telegram.org в operator-инструкциях |
| CHANGELOG.md | 2 | history |
| docs/ | 60 | ADR-014, ADR-016, release-notes, diagnostics |
| examples/ | 61 | examples/v15-sample-run/telegram/, examples/report-delivery/telegram/ |
| failure-corpus/ | 22 | failure cases с Telegram-сценариями |
| references/telegram-*-policy.md | 6 файлов | Telegram-named policy docs |
| templates/telegram/*.txt | 7 файлов | Telegram-shaped templates |

Все они — template/policy/sample, не код-путь. Нарушают agent-native интент по именованию, но runtime от них не зависит (Phase 5 проверит import graph).

## Свод

- Контракты-as-data: 3 JSON-контракта явно содержат backend-name "telegram". Это нарушает agent-native интент — выдаёт привилегированное знание о конкретном backend на уровне runtime/contract.
- Политики, плейбуки, профили валидации, схемы — полностью чистые. Это сильный сигнал, что нейтральность была введена сознательно для одной части системы, но не для контрактов и не для документации.
- Документация и templates — содержат значительный backend-name leak. По плану — фиксируется, не блокирует.
