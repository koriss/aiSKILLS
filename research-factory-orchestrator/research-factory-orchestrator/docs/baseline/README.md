# Baseline (agent session)

- **S0 / preflight**: captured in baseline summary + release notes semantic diff.
- **S1 / backup diff**: no frozen pre-v19 tree in-repo; semantic table in release notes.
- **S2 / atomic install**: not executed (workspace-local skill tree only).
- **S3 / L0 validators**: run `python3 -S scripts/validate_skill.py` from skill root when shell available.
- **S4 / smoke**: `python3 -S scripts/rfo_runtime_core.py smoke --provider telegram`.
- **S5 / adversarial**: failure corpus via `rfo_runtime_core.py failure`; host bypass fixture under `tests/host-integration/`.
- **S6 / aggregate**: baseline summary artifact.
- **S7 / leak check**: confirm edits stay under `research-factory-orchestrator/`; no `sudo` used.
