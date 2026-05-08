# Static V19 Cleanup Inventory

- Timestamp (UTC): `20260508T182007Z`
- Branch: `cleanup/v19-only-version-purge`
- Base commit at start: `db950db`
- Scope root: `/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator`
- Canonical `/opt/openclaw`: not touched

## Baseline

- `rg -o "v1[0-8]" . | wc -l` => `440`
- Working tree at start: clean

## Planned Work Buckets

1. Remove legacy compat layer and v18 compatibility validators/contracts.
2. Remove version-named corpora/examples/references for v14-v18.
3. Rewrite `SKILL.md` to thin v19 overlay and clean `SKILL-core.md`.
4. Clean scripts/runtime/contracts/templates/docs from v17/v18 markers.
5. Remove v19.2.x repro/phase5 smoke scripts and clean references.
6. Implement v19.3 runtime blockers fixes (B1-B5) in `render`, `collector`, `build_package`, V6.
7. Run validation/smoke suite and regenerate `release-validation-transcript.json`.
8. Produce two commits:
   - Commit 1: purge
   - Commit 2: runtime blockers fixes
