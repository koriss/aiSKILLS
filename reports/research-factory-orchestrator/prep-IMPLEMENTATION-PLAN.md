
# Implementation Plan for v12-report-delivery-system

## Phase 1 — Semantic report model

Add schemas:

```text
schemas/report.schema.json
schemas/report-summary.schema.json
schemas/report-section.schema.json
schemas/report-component.schema.json
schemas/report-archetype.schema.json
schemas/telegram-summary.schema.json
schemas/telegram-message-plan.schema.json
schemas/telegram-message.schema.json
schemas/telegram-delivery.schema.json
```

## Phase 2 — Standalone HTML renderer

Add:

```text
templates/full-report-standalone-template.html
templates/assets/report-theme.css
templates/assets/report-enhancements.js
scripts/render_standalone_html_report.py
scripts/validate_standalone_html.py
```

Renderer may use separate CSS/JS internally, but delivered `full-report.html` must inline everything required.

## Phase 3 — Component library

Add:

```text
templates/components/
```

## Phase 4 — Archetype registry

Add:

```text
templates/archetypes/report-archetypes.json
scripts/select_report_archetype.py
```

## Phase 5 — Telegram delivery

Add:

```text
templates/telegram/plain-*.txt
scripts/render_telegram_summary.py
scripts/split_telegram_messages.py
scripts/validate_telegram_delivery.py
scripts/validate_telegram_plain_text.py
scripts/validate_no_large_telegram_tables.py
scripts/validate_telegram_message_lengths.py
```

## Phase 6 — Final gates

Final delivery is invalid unless:

```text
full-report.html is standalone
telegram messages are plain text
telegram messages are within length limits
no large tables in telegram
summary contains no new facts
verified claims have inline citations
HTML is mobile-first
report package includes semantic JSON + rendered HTML + telegram plan
```
