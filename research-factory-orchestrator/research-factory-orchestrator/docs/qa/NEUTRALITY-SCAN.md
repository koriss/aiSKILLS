# Neutrality scan (vendor-token gate)

This file records the markdown scan required by plan todo `neutral-06-gate-rg`.

## Command

```bash
cd research-factory-orchestrator/research-factory-orchestrator
rg -n "openclaw|OpenClaw|telegram|Telegram|/opt/openclaw|~/.openclaw" \
  SKILL.md AGENTS.md docs/runtime-paths.md docs/qa \
  docs/adr/ADR-016-compute-vs-delivery-split.md \
  docs/adr/ADR-017-rfo-triple-deliverables.md \
  docs/adr/ADR-RFO_PORTABLE.md
```

## Allowed residual matches

- Transitional compatibility filename references: `verify_openclaw_run.py`.
- Historical archive filenames in `docs/qa/RFO-VERSION-QUALITY-MATRIX.md` (ZIP inventory evidence).

Any other match in the scanned scope should be treated as a neutrality regression.
