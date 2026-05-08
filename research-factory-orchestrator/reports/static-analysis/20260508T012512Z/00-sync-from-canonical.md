# Pre-Phase: sync project ← canonical

- **Timestamp (UTC)**: `20260508T012512Z`
- **Source (canonical)**: `/opt/openclaw/data/workspace/skills/research-factory-orchestrator/`
- **Destination (project)**: `/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/`
- **Skill version (post-sync)**: `19.3` (`runtime_contract=19.3`, `failure_corpus_index=19.2.1`)
- **Branches**:
  - Snapshot of pre-sync worktree: `wip/snapshot-pre-sync-20260508T012512Z` (commit `6ba4165`)
  - Sync target: `feat/v19-3-sync-from-canonical` (branched from `feat/v19-2-0-runtime-truth` @ `a1bc11e`)
- **Push policy**: nothing pushed; commits stay local until explicit user command.

## Why

The project directory `_projects/aiSKILLS/research-factory-orchestrator/` (referred to below as "project") had drifted from the deployed canonical RFO skill at `/opt/openclaw/data/workspace/skills/research-factory-orchestrator/`. Static analysis must run on the **same** code that is actually deployed, so we synchronize first, before lifting any analyzer.

## Pre.1 — snapshot of worktree

Before touching anything we created a safety branch `wip/snapshot-pre-sync-20260508T012512Z` from `feat/v19-2-0-runtime-truth` and committed every dirty path:

- 21 modified
- 13 deleted
- 123 untracked-then-added (includes `.tmp-exec-runs/` rfo run artifacts that the project keeps unignored)

Snapshot commit: `6ba4165 chore(rfo): snapshot worktree before canonical sync`. No source edits were made.

## Pre.2 — sync branch

Created `feat/v19-3-sync-from-canonical` from clean `feat/v19-2-0-runtime-truth` (`a1bc11e`). Worktree at this point matches the last committed state on that branch.

## Pre.3 — rsync

Command:

```bash
rsync -av --delete \
  --exclude='.tmp-exec-runs/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='release-artifacts/' \
  --exclude='release-validation-transcript.json' \
  --exclude='composition-audit-report.json' \
  --exclude='coverage-report.json' \
  --exclude='tools/agent_telegram/' \
  --exclude='.venv/' \
  --exclude='.git/' \
  --exclude='reports/' \
  /opt/openclaw/data/workspace/skills/research-factory-orchestrator/ \
  /home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/
```

Logs: `00-rsync-dry-run.log`, `00-rsync-actual.log` (1367 entries each).

### Exclusions and why they were applied

| Path / pattern | Reason |
|---|---|
| `.tmp-exec-runs/` | RFO run artifacts; bulky, not skill code. |
| `__pycache__/`, `*.pyc` | Python bytecode caches. |
| `release-artifacts/` | Project-side release tarballs; not part of deployed skill. |
| `release-validation-transcript.json` | Release-time artifact, not source. |
| `composition-audit-report.json`, `coverage-report.json` | Validator outputs, not source. |
| `tools/agent_telegram/` | Operator-side tooling kept only in the project, per plan. |
| `.venv/` | Local Python venv for analyzer tooling (Phase 0). |
| `.git/`, `reports/` | Repo metadata and analysis output respectively. |

## Pre.4 — diff summary

`git diff --stat HEAD` (snapshot in `00-git-diff-stat.txt`):

- 24 files changed, 729 insertions(+), 450 deletions(-)

`git status -s` buckets (snapshot in `00-git-status.txt`):

- 21 **M** (modified)
- 3 **D** (deleted: `providers/telegram/telegram_delivery_adapter.py`, `scripts/_smoke_telegram_real_send.py`, `scripts/_smoke_telegram_agent_interface.py`)
- 19 **??** (new from canonical, includes `scripts/run_rfo_with_web_search.py` — flagged in advance as an agent-native candidate finding for Phase 2)

### Notable removals

- `providers/telegram/telegram_delivery_adapter.py` — vendor-specific delivery adapter. Aligns with the agent-native goal: skill must not embed Telegram knowledge.
- `scripts/_smoke_telegram_real_send.py`, `scripts/_smoke_telegram_agent_interface.py` — Telegram-specific smoke tests removed alongside the adapter.

### Notable additions

- `scripts/run_rfo_with_web_search.py` — kept on disk after sync (canonical contains it, so the project must mirror it for honest analysis), but pre-flagged as a Phase 2 finding because the file name itself signals a hardcoded backend.
- `scripts/run_rfo_full_research.py` — pre-flagged for Phase 2 review as well.
- `scripts/_test_mvr_profile_seed_only_disclosure.py` — disclosure test, neutral.
- `runtime/artifact_execute_impl.py` — v19.3 artifact-only execute path. Already known.
- `docs/adr/ADR-016-compute-vs-delivery-split.md` — new ADR documenting the compute/delivery split.

### Notable modifications

- `runtime/cli.py` — picked up `--profile` / `--seed-urls` argument parsing (the patch I shipped to canonical on 7 May).
- `contracts/provider-capabilities.json`, `contracts/provider-contract.json` — capability surface updates.
- `runtime/adapter_impl.py`, `runtime/outbox_impl.py`, `runtime/validate_impl.py`, `runtime/worker_impl.py` — runtime alignment to v19.3.
- `scripts/build_research_package.py`, `scripts/interface_runtime_adapter.py`, `scripts/outbox_delivery_worker.py`, `scripts/rfo_runtime_core.py`, `scripts/runtime_job_worker.py`, `scripts/validate_*.py`, `scripts/verify_openclaw_run.py` — script-side companions.
- `SKILL.md`, `CHANGELOG.md` — documentation alignment.

## Pre.5 — commit

Commit message used:

```
chore(rfo): sync project workspace ← canonical /opt v19.3

Source: /opt/openclaw/data/workspace/skills/research-factory-orchestrator/
Skill version: 19.3 (runtime_contract 19.3, failure_corpus_index 19.2.1)
```

Hash: see `00-commit-info.txt` once Pre.5 lands.

## Pre.6 — protocol artifact

This file plus the rsync logs and git status snapshots constitute the sync protocol. Subsequent phases will write peer files into the same `reports/static-analysis/20260508T012512Z/` directory and a final commit will land them all together.
