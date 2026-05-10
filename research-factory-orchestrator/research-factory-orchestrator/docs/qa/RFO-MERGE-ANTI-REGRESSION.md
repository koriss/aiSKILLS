# Merge anti-regression checklist (plan §0A)

Use before merging QA / playbook / verifier changes.

## Anti-goals (do not reintroduce)

- **v18-style synthetic claims** without explicit `meta.origin` markers where required by validators.
- **Messenger/channel API** code paths inside the canonical skill runtime (delivery stays host-owned; ADR-016).
- **Multiple unrelated host deploy edits** in one changeset — one instance / one owner note per MR.
- **Relay E2E** as default CI without `RFO_RELAY_SMOKE` or staging infra (see assertion matrix).

## Doc hygiene

- **Playbook** links to [`SKILL-core.md`](../../SKILL-core.md), [`PROFILE_DEFAULTS.md`](../PROFILE_DEFAULTS.md), and `--help` — avoid duplicating full env tables inline.
- **Embedded presets / MediaWiki** branches: document only after confirming **live** code paths in `scripts/run_rfo_full_research.py`; otherwise label **secondary / expert-only**.

## Verifier / contracts

- After contract or path tweaks: `python3 -S scripts/validate_skill.py` from package `cwd`.
- After `runtime/report_html.py` edits: `python3 -m unittest tests.test_report_html_citations`.

## Packet vs work units

- **`RFO_SOURCE_PACKET` does not create `work-units.json`.** `total_planned=0` with relay + packet can be canonical until impl-21 owner decision — not automatically a relay bug ([RFO-FULL-RESEARCH-PLAYBOOK](./RFO-FULL-RESEARCH-PLAYBOOK.md)).

## Honesty tooling

- Use **`verify_skill_run_claims`** (`validator_id` in JSON); `verify_openclaw_run` remains a transitional entrypoint filename only.
