# OpenClaw gateway — RFO slash operator checklist

**Scope:** host deploy (typically `/opt/openclaw` or your compose tree). This file lives in the **skill repo** so operators have one URL to paste into runbooks; it does **not** patch the gateway from here.

## A3 — Recommended `RFO_BRIDGE_WORKER_*` (opt-openclaw, long dossier)

Defaults are defined in `scripts/run_rfo_with_web_search.py` (not overridden here):

| Variable | Default | Meaning |
|----------|---------|--------|
| `RFO_BRIDGE_WORKER_TIMEOUT` | `600` | Per **single** `runtime_job_worker.py` subprocess wall-clock cap (seconds). |
| `RFO_BRIDGE_WORKER_RETRIES` | `12` | Max claim attempts when worker returns `claimed: false` (e.g. `lease_present`, `no pending`). |
| `RFO_BRIDGE_WORKER_BACKOFF` | `0.35` | Base sleep between retries; actual sleep is `backoff + 0.12 * attempt`. |

**Worst-case upper bound** (pathological hung worker each attempt): roughly  
`RFO_BRIDGE_WORKER_RETRIES × RFO_BRIDGE_WORKER_TIMEOUT` **plus** adapter/relay/post steps. Example: defaults → on the order of **2 hours** before the bridge gives up on the worker loop alone — gateway subprocess budget must **exceed** that if you never want SIGTERM mid-bridge.

**Tuning without forking code:** for a single long-running worker and heavy dossier, operators often **raise** `RFO_BRIDGE_WORKER_TIMEOUT` and/or `RFO_BRIDGE_WORKER_RETRIES`, then **match** gateway timeout (B1). Shorter smoke stacks can keep defaults.

## B1 — Subprocess budget vs bridge wait loop

- Native `/research_factory_orchestrator` should invoke the skill’s **`python3 -S scripts/rfo_execute.py`** (same argv as the legacy spelled-out `run_rfo_with_web_search.py` command).
- The bridge may wait for **`runtime_job_worker.py`** longer than a default “short skill” timeout. If the gateway **SIGKILL/SIGTERM** the child before the worker claims the job or before stdout handoff, the user sees a broken pipe — not a completed RFO.
- **Action:** set the gateway / skill runner timeout using **A3** table (at minimum: cover `RFO_BRIDGE_WORKER_RETRIES × RFO_BRIDGE_WORKER_TIMEOUT` pessimistic bound + ~15–30 min for relay/render/package). Document the chosen value next to your compose service.

## B2 — Plain subagent fallback

- **Anti-pattern:** on timeout, `lease_present`, or “worker busy”, spawning a **plain research subagent** for the *same* `/research_factory_orchestrator` user intent. That produces chat prose without the run-dir gate bundle and violates the skill prohibition in `SKILL.md`.
- **Preferred:** reply with **queue state** (`run_id`, link to `rfo-runs/...`, “still running”), optionally tail **`observability-events.jsonl`** (`bridge.worker_poll`), and point to **`docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`**.
- **Escape hatch:** a *different* user-facing command for “quick unstructured recap” so evidence lanes do not mix with artifact-only RFO.

## B3 — Audit JSONL (optional)

- For forensics, append **gateway-owned** events (skill subprocess start, exit code, stderr tail hash, SIGTERM) under `workspace/audit/` — analogous to post-delivery audit already used for native Telegram sends. Schema is host-defined; keep PII out.

## Cross-links

- Skill map: `docs/runtime-paths.md`
- Lease triage: `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md`
- Agency / degraded modes rationale: `docs/adr/ADR-020-vacuum-of-agency-degraded-modes.md`
