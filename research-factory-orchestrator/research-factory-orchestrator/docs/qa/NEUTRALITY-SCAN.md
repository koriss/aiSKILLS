# Neutrality scan (vendor-token gate)

This file records the markdown scan required by plan todo `neutral-06-gate-rg`.
It is also the canonical residual allowlist for `repo-neutrality-full-sweep`.

## Command

```bash
cd research-factory-orchestrator/research-factory-orchestrator
rg -n "openclaw|OpenClaw|telegram|Telegram|/opt/openclaw|~/.openclaw|verify_openclaw_run\.py" \
  --glob "*.md" \
  AGENTS.md SKILL.md CHANGELOG.md contracts docs kb
```

## Allowed residual matches

- Transitional compatibility filename references to `verify_openclaw_run.py`.
- Historical ZIP/archive inventory names in `docs/qa/RFO-VERSION-QUALITY-MATRIX.md`.
- Explicitly frozen historical notes:
  - `docs/release-notes/v19.*.md`
  - `docs/adr/ADR-014-telegram-operator-control-plane.md`
  - `docs/project-handoff-v18.1.1.md`
  - `docs/operations/safe_install_openclaw_v19_2.md`
  - `kb/propaganda-io/**` frozen path notes

Any other match in the scanned scope should be treated as a neutrality regression.
