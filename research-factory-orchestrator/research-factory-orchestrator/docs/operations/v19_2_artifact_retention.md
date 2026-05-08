# v19.2.0 — Artifact retention (recommendation, not enforced)

Long-running agent hosts accumulate hundreds of `runs/*` trees and smoke roots.
v19.2.0 **does not** enforce retention in code.

## Recommended policy (operator)

1. Keep **last 3** production-cycle run directories per workspace root.
2. Archive older runs monthly (tar.gz to cold storage) before deletion.
3. Never delete the latest **release-validation-transcript.json** companion evidence
   until a newer green release exists.

## OpenClaw note

If the skill is installed under `/opt/openclaw/skills/research-factory-orchestrator`,
apply the same policy at the **guest** boundary (`_guests/` zip remains canonical).
