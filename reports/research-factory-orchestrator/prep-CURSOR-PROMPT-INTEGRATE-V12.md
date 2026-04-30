
# Cursor Prompt — Integrate v12 Report Delivery System

You are editing the OpenClaw skill `research_factory_orchestrator`.

Goal: integrate the v12 report delivery system prep kit into the existing v11 self-contained KB skill.

Hard requirements:

```text
1. Final full-report.html must be standalone single-file HTML.
2. No external CSS/JS/fonts/images in delivered HTML.
3. HTML must be mobile-first and desktop-readable.
4. Telegram delivery must be plain text by default.
5. Do not use Telegram HTML parse_mode or Markdown parse_mode as required output.
6. No large tables in Telegram messages.
7. Telegram summary must be semantically split across multiple messages if long.
8. Summary must not introduce new facts absent from verified/allowed claims.
9. Full report remains HTML; Telegram is only mobile briefing + file delivery.
10. research-package.zip remains required.
```

Tasks:

```text
1. Copy references/* into skill references/.
2. Copy schemas/* into skill schemas/.
3. Copy templates/* into skill templates/.
4. Copy scripts/* into skill scripts/.
5. Add v12 references to SKILL.md.
6. Add report semantic model artifacts to mandatory research package.
7. Add Telegram delivery artifacts to mandatory research package.
8. Update final-answer gate:
   - standalone_html_validated
   - telegram_delivery_validated
   - telegram_plain_text_only
   - no_large_telegram_tables
   - summary_no_new_facts
9. Add render step:
   semantic-report.json -> full-report.html standalone
10. Add Telegram render step:
   telegram-summary.json -> telegram-message-plan.json -> telegram-message-N.txt
11. Add validators to validation transcript.
12. Update installation/update docs.
13. Package as v12-report-delivery-system.
```

Do not remove v11 durable work-units, embedded KB, INT coverage, source provenance, wiki citations, or research-package.zip.
