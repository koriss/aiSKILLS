# v18.3.2 baseline (agent session)

- **S0 / preflight**: captured in `v18.3.2-baseline-summary.json` + release notes semantic diff.
- **S1 / backup diff**: no frozen v18.3.1 tree in-repo; semantic table in `docs/release-notes/v18.3.2-semantic-diff.md`.
- **S2 / atomic install**: not executed (workspace-local skill tree only).
- **S3 / L0 validators**: run `python3 -S scripts/validate_skill.py` from skill root when shell available.
- **S4 / smoke**: `python3 -S scripts/rfo_v18_core.py smoke --provider telegram`.
- **S5 / adversarial**: failure corpus via `rfo_v18_core.py failure`; host bypass fixture under `tests/host-integration/`.
- **S6 / aggregate**: `v18.3.2-baseline-summary.json`.
- **S7 / leak check**: confirm edits stay under `research-factory-orchestrator/`; no `sudo` used.
