# Role: user facts collection

## Purpose

Gather **user-supplied** facts and constraints before a research run. This file is **not** a second knowledge base; it structures input only.

## Input contract

- **Required:** clear research question or task statement; jurisdiction / language if material; hard deadlines.
- **Forbidden:** asking the model to invent citations; pasting unverified claims as “verified” without evidence markers.

## Output contract

- Bullet list of **facts the user asserts** vs **questions for the run**.
- Explicit “unknowns” the run should not paper over.

## Evidence boundary

Per **ADR-001**, evidence for the dossier comes from **run artifacts** (`sources.json`, claims registry, evidence cards) — not from this prompt alone.
