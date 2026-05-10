# Neutrality scan (vendor-token gate)

This file records the markdown scan required by plan todo `neutral-06-gate-rg`.
It is also the canonical residual allowlist for `repo-neutrality-full-sweep`.

## Canonical RFO deep analysis bundle (remediation / incident)

For **end-to-end failure diagnosis**, queue/lease incidents, truth vs delivery semantics, and contract alignment — use this documentation set (do not rely on chat summaries alone):

| Doc | Purpose |
|-----|---------|
| [RFO-DEEP-ANALYSIS-2026-05.md](./RFO-DEEP-ANALYSIS-2026-05.md) | Incident timeline, fault taxonomy, critical findings, repro matrix, blast radius |
| [RFO-REMEDIATION-ROADMAP.md](./RFO-REMEDIATION-ROADMAP.md) | Workstreams A–E, rollback, acceptance |
| [RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md](./RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md) | 5-minute triage + safe lease recovery |
| [RFO-TRUTH-CONTRACTS-ALIGNMENT.md](./RFO-TRUTH-CONTRACTS-ALIGNMENT.md) | Runtime → contracts → validators → report mapping and drift pairs |

The **assertion ↔ command** checklist for regression checks is [`assertion-command-matrix.md`](./assertion-command-matrix.md).

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
