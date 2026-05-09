# ADR-017 — HTML full-report template, wiki citations, IO section

## Status

Accepted (runtime implementation).

## Context

`render_all` historically emitted minimal inline HTML. Investigative sections and wiki-style `[n]` → `#ref-n` citations lived only in [`examples/report-delivery/sample-full-report.html`](../../examples/report-delivery/sample-full-report.html). [`templates/full-report-template.html`](../../templates/full-report-template.html) was unused.

## Decision

1. **Single module** [`runtime/report_html.py`](../../runtime/report_html.py) builds `report/full-report.html` by filling [`templates/full-report-template.html`](../../templates/full-report-template.html) with escaped fragments derived **only** from run-dir JSON (claims, sources, evidence, graph, memo, io, audit, optional `io/*.json`).
2. **Citation contract**
   - Sources are numbered in **stable sorted order** by `source_id` → indices `1…N`.
   - Claim cards render `<sup class="ref-marker"><a href="#ref-{n}">[n]</a></sup>` for each `source_id` in `claim.support_set[]`.
   - References section is `<ol id="references-list" class="source-list">` with `<li id="ref-{n}">…</li>` (URLs and metadata from source objects).
   - Claims without support emit a visible **no source anchor** chip; no fake `[n]`.
3. **IO / propaganda**: dedicated section from `report/io-propaganda-check.json` plus optional [`io/narrative-map.json`](../../io/) (and related files) when present.
4. **Embedded proof**: JSON `<script type="application/json">` blocks appended before `</body>` (same filenames as before, plus `report/semantic-report.json`).
5. **CLI** [`scripts/render_full_html_report.py`](../../scripts/render_full_html_report.py) calls `build_full_report_html_from_run_dir` — same artifact contract as skill `render_all` (does not overwrite `semantic-report.json`).

## Consequences

- Human-readable report and validators can rely on one HTML shape.
- Empty investigative slots say explicitly that artifacts are missing (no invented prose).
