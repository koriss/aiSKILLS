# RFO: LLM pipeline checkpoints (MD-first)

Use when a model (Cursor agent, guest agent, or operator copilot) sits **between** deterministic RFO steps. The model must **not** invent `run_dir`, reorder gates, or propose a second HTML render straight from JSON while the strict MD-first path is in effect.

## Layer A — bootstrap (once per session or per investigation)

Paste or paraphrase from repo truth only:

- **Flow:** `run_dir` JSON artifacts → `report/full-report.md` → `report/full-report.html` (HTML is **only** derived from the MD string).
- **Canonical relative paths:** `report/full-report.md`, `report/full-report.html`, `chat/01-analysis.md`, `chat/02-facts.md`, `final-answer-gate.json`, `result-manifest.json` (all under the **same** `run_dir` from the handoff).
- **MUST NOT:** guess `run_dir` from task text; substitute paths from chat memory; skip MD; render HTML from JSON in parallel with MD-first.

Sources: `SKILL.md`, `docs/runtime-paths.md`, ADR-016 / ADR-017.

## Layer B — stage checkpoint (before each next action)

Give the model only:

1. **On disk now:** list paths that exist (or last command exit + tail).
2. **Next single deterministic step:** one command or one file read (e.g. open `report/full-report.md`).
3. **Forbidden on this step:** e.g. “do not run legacy `build_full_report_html_from_run_dir` for the shipped dossier” unless troubleshooting an explicit legacy path.

If context drifts, repeat one short Layer A paragraph (paths + MUST NOT), not the full skill.

## Responsibility boundary

Building `full-report.md` / `full-report.html` is **code** (`runtime/report_md.py`, `runtime/report_html.py`, validators). LLM prompts are for **navigation**, operator explanation, and manual coordination — not replacing the renderer ad hoc.
