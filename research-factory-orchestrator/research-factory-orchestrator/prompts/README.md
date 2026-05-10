# prompts/ — supported operator prompts (narrow surface)

Fragments under `prompts/` are **maintained prompts** for **second-pass agents** — not validators, not a second KB. Canonical runtime contracts remain **`SKILL.md`**, **`SKILL-core.md`**, `contracts/`, and ADRs.

## Role index (`prompts/roles/`)

| File | Role |
|------|------|
| [`roles/user-facts-collection.md`](./roles/user-facts-collection.md) | Structure **user-supplied facts** before a run (input contract → ADR-001). |
| [`roles/user-task-summary.md`](./roles/user-task-summary.md) | Short **task recap** respecting channel truncation; must not invent relay proof. |
| [`roles/analytics-from-run-artifacts.md`](./roles/analytics-from-run-artifacts.md) | Critique/analysis using **existing** bundle files only. |

**Downstream invocation:** consuming agents read paths from **`agent-handoff/bundle-manifest.json`** after a successful compute handoff (`impl-24`). Legacy worker prompts elsewhere in this folder may still exist for fixtures — prefer the roles above for human-facing workflows.
