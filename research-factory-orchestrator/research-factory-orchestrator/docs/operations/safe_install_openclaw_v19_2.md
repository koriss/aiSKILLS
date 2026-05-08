# Safe install — v19.2.0 into `/opt/openclaw` (operator checklist)

> **Requires explicit host approval.** Do not run destructive commands without a
> backup and a maintenance window.

## Preconditions

1. Confirm **single OpenClaw instance** policy (see workspace rule
   `openclaw-single-instance.mdc`).
2. Record current skill version: read `runtime/version.json` in the live tree.
3. Build or obtain the flat workspace zip
   `_guests/openclaw-research-factory-orchestrator-v19.2.0-runtime-truth-restoration-workspace.zip`
   and verify `release-manifest.json` **SHA256** inside the zip.

## Steps (no sudo in-repo automation)

1. **Backup** — `cp -a /opt/openclaw/skills/research-factory-orchestrator /opt/openclaw/_backup/rfo-$(date +%F)` (adjust paths to your layout).
2. **Atomic replace** — unpack zip to a temp dir, then `mv` the new tree over the
   old skill directory in one rename (fail-closed rollback = restore backup).
3. **Allowlist** — refresh `agent.skills` / host allowlists to include any new
   `tools/agent_telegram/` entrypoints you expose.
4. **Sanity** — run slash-command smoke paths documented in `SKILL-core.md`.

## Post-install evidence

- Attach `release-validation-transcript.json` from the build host.
- Attach `sha256sum` of the workspace zip (or cite the in-zip manifest digest).
