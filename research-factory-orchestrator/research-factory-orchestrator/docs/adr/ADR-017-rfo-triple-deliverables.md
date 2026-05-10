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

## Gateway (host-owned)

For host-channel delivery (`skill-artifact-delivery.ts`-style integration), artifacts with `role` `analysis` or `facts` and `media_type` containing `markdown` are delivered as text messages/chunks; HTML and zip are delivered as file attachments. Thread/reply metadata may be applied by host policy when provided.

## Skill boundary

Compute-only path does not open channel sessions; the gateway performs delivery after parsing the stdout handoff marker.
