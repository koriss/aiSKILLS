# ADR-017: RFO triple deliverables (analysis + facts + HTML)

## Status

Accepted — 2026-05-09

## Context

The skill should produce three user-facing artifacts per run:

1. `chat/01-analysis.md` — analytical memo plus IO/propaganda context (no separate “IO-only” chat file).
2. `chat/02-facts.md` — numbered claims with statuses and URLs where available; `confirmed`/`probable` without URL-backed sources are downgraded (`facts_gate`).
3. `report/full-report.html` — full HTML report; embedded JSON proof blocks remain at the bottom of the document.

Legacy chat files `message-003-io-propaganda-check.txt` and `message-004-files.txt` are no longer generated.

## Machine contract

- `result-manifest.json` lists the three artifacts (plus optional `package/research-package.zip`). `primary_text` is excerpted from `01-analysis.md`.
- `result.json` duplicates deliverables and `quality` for diagnostics (gateway continues to read `result-manifest.json`).

## Outbox

Canonical events: `OUT-0001` / `OUT-0002` (Markdown chat payloads), `OUT-0005` (HTML), `OUT-0006` (zip).

## Gateway (OpenClaw)

For Telegram delivery (`skill-artifact-delivery.ts`), artifacts with `role` `analysis` or `facts` and `media_type` containing `markdown` are sent as `sendMessage` (chunked ≤4000 chars). HTML and zip use `sendDocument`. The first outbound message may use `reply_to_message_id` when provided.

## Skill boundary

Compute-only path does not open Telegram sessions; the gateway performs delivery after parsing the stdout handoff marker.
