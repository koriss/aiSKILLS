# RFO — version / layout / quality matrix (archives + canonical)

**Purpose:** compare **historical workspace ZIPs** (read-only ideas under `/home/kazak/_projects/_tmp/rfo/`) with the **canonical git package** behavior. Do **not** restore code from archives into the repo.

**Normative contracts:** [ADR-001](../adr/ADR-001-v19-pragmatic-rigor.md) (evidence boundary), [ADR-016](../adr/ADR-016-compute-vs-delivery-split.md) (compute vs host delivery), [ADR-017](../adr/ADR-017-artifact-only-release.md) (artifact-only release expectations where applicable), [ADR-018](../adr/ADR-018-bridge-handoff-contract-and-portable-paths.md) (bridge stdout + path guard).

## Canonical row (git package)

| Artifact | Expectation |
|----------|-------------|
| Layout | Inner package: `research-factory-orchestrator/research-factory-orchestrator/` (see [RFO-CANONICAL-WORK-ROOTS](./RFO-CANONICAL-WORK-ROOTS.md)) |
| Handoff | Single stdout line `__RFO_SKILL_AGENT_HANDOFF__=`; progress on stderr (ADR-016/018) |
| Deliverables | `result-manifest.json`, `chat/*.md`, `report/full-report.html`, `agent-handoff/bundle-manifest.json` |
| Honesty harness | `scripts/verify_skill_run_claims.py` (`validator_id` in JSON) |
| HTML truth banner | `feature-truth-matrix.json` excerpt embedded in report HTML + analysis MD (scaffold values) |

## Historical ZIP inventory (prefix patterns)

Paths below are **inside** each archive (`unzip -l` sample, 2026-05-10). Sizes are approximate from `ls -la`.

| Archive | ~Size | Top path prefix | Notes |
|---------|------:|-----------------|-------|
| `openclaw-research-factory-orchestrator-v11-self-contained-kb-workspace.zip` | 2.8M | `skills/research-factory-orchestrator/…` | Large embedded `kb/propaganda-io`; **legacy** KB-in-zip layout |
| `openclaw-research-factory-orchestrator-v12-report-delivery-prep.zip` | 44K | flat workspace (`examples/`, `case-library/` at zip root) | Prep bundle, not full skill tree |
| `openclaw-research-factory-orchestrator-v12-report-delivery-system-workspace.zip` | 2.9M | `skills/research-factory-orchestrator/…` | Workspace layout with `reports/…` |
| `…-v17.x–v19.x-*-workspace.zip` | ~3–19M | `skills/research-factory-orchestrator/…` | Progressive validator/runtime hardening snapshots |
| `openclaw-research-factory-orchestrator-v7-proof-workspace.zip` | 77K | mixed | Proof-era bundle; **context only** vs v19 pragmatic rigor |
| `openclaw-research-factory-orchestrator-workspace.zip` | 11K | minimal | Early stub |

**Rule:** ZIP rows are **not** compatibility promises. For behavior, always read **`runtime/version.json`** and run **`validate_skill`** on canonical checkout.

## v7-proof vs canonical (diff intent only)

Reading **v7-proof** ZIPs informs **historical regressions we avoid** (synthetic “rich” narratives, path chaos). **No file** from v7 should be copied into the canonical tree; port **invariants** only after reading current code (plan §6).

## Upstream-only items (not patched in this repo)

- **Gateway stdout scan** — see [ADR-019](../adr/ADR-019-host-handoff-stdout-scanning.md).
- **Optional manifest-first delivery text** — host product choice; must match `skill-result` schema.
