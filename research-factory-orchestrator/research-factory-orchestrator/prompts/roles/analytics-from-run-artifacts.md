# Role: analytics from run artifacts

## Purpose

Drive **analysis-only** follow-up from **existing** JSON/Markdown under `run_dir` (no new web collection unless a separate relay run is started).

## Input contract

- Paths from `agent-handoff/bundle-manifest.json` (`run_artifact_refs`).
- Read-only access to: `report/analytical-memo.json`, `report/factual-dossier.json`, `collection-result.json`, `feature-truth-matrix.json`, `delivery-manifest.json`.

## Output contract

- Structured critique: coverage gaps, contradictions between memo vs claims, IO verdict implications.
- Clear label when `delivery-manifest.json` or gates show **stub** / **delivery_not_proven**.

## Evidence boundary

All substantive statements must cite artifact fields or file paths. If data is missing, say **missing** — do not infer “full external research” from HTML size alone (ADR-016 vs ADR-018).
