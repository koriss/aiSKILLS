# Role: user task summary

## Purpose

Produce a **short** summary of what the user asked for, suitable for a second agent pass or handoff channel with tight context limits.

## Input contract

- User message + optional `task_excerpt` from the handoff capsule.
- Optional paths to `chat/01-analysis.md` and `report/analytical-memo.json` for alignment checks.

## Output contract

- 5–12 bullet points: objective, scope, exclusions, success criteria.
- Explicit statement if the run was **seed-only** or **relay-backed** (read from `collection-result.json` / `feature-truth-matrix.json`, do not invent).

## Evidence boundary

Do not restate external URLs as “confirmed” unless they appear in run artifacts with matching claim support (ADR-001).
