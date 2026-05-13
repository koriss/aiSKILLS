---
name: RFO agent-executable single-behavior in-repo
overview: >
  Deterministic RFO contract for IDE/CLI agents with only repo-local tools.
  Canonical production requires explicit argv (--runs-root, relay base) and
  fail-fast when dependencies are missing. In-repo validation uses an explicit
  test_fixture harness. Blocked external dependency must never be replaced by
  ordinary web_search or synthetic research output.
isProject: false
---

# RFO: agent-executable single behavior (in-repo)

**Work boundary:** changes live only under the inner skill package tree (see repo rules).  
**Companion (narrower slice):** `docs/plans/PLAN-agent-executable-contract.md`.

## 0. Goal

Make RFO **honestly executable** on the tools an agent actually has (read/search/shell/python/tests), not by implying production infra (OpenClaw, Docker, SearXNG DNS, gateway relay) exists.

## 1. Three execution modes

1. **Canonical production** — explicit `--runs-root`, relay base, reachable contract; `production_research=true` only when preflight is clean.
2. **`test_fixture`** — `RFO_RUN_EXECUTION_MODE=test_fixture|fixture|ci`; allows relaxed tmp / non-canonical layout env keys; `production_research=false`; must never be presented as full web research.
3. **Blocked external dependency** — missing argv runs-root, missing relay, or strict forbidden env → non-zero preflight; machine-readable `blocked_dependency` in `rfo-effective-config-v1`.

## 2. Public CLI

Single operator-facing research launcher: **`python3 -S scripts/rfo_execute.py`**.  
`scripts/run_rfo_with_web_search.py` is the **bridge implementation** (loaded by the façade).  
`scripts/run_rfo_full_research.py` — **grave marker**, exit **2**, no redirect.

## 3. Config resolution (shipped incrementally)

- **Argv `--runs-root`** required for canonical (no implicit `~/.openclaw/.../rfo-runs` / `~/rfo-runs` as silent production default).
- **`RFO_RUN_EXECUTION_MODE=test_fixture`** restores legacy resolution for CI and documents `fixture_mode` / `search_mode=fixture_relay` in effective-config.
- **Forbidden env** (smoke / legacy allow) fails canonical; **relaxed in fixture** only: `RFO_ALLOW_TMP_RUNS_ROOT`, `RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT`.
- **Effective-config** fields: `run_execution_mode`, `production_research`, `fixture_mode`, `search_mode`, `blocked_dependency` (see `contracts/rfo-effective-config-v1.schema.json`).

## 4. Post-run answer contract (agent)

After a successful compute exit: read **primary report** (`report/full-report.md` / `.html`), **`final-answer-gate.json`**, grounding when required, delivery truth when claiming delivery. User-facing synthesis **first**; validator metrics **tail** only — never substitute metrics for substantive answer.

## 5. Phasing (PR-sized)

1. Docs + contracts + doc-grep validator (this file, `docs/rfo-env-classification.md`, `validate_agent_executable_doc_grep.py`).
2. Unified config resolution + startup summary + preflight (ongoing in `runtime/config_resolution.py`).
3. Runtime cleanup: legacy markers, smoke removal from canonical path, secondary relay deprecation messaging.
4. Fixture/blocked/answer-readiness tests and regression fixtures.

## 6. Acceptance (incremental)

- [x] Effective-config schema includes execution mode / production flags / blocked dependency.
- [x] Canonical missing `--runs-root` argv → `blocked_external_dependency` + `runs_root_argv`.
- [x] `test_fixture` marks `production_research=false`.
- [x] Doc-grep blocks copy-paste `python3 -S scripts/run_rfo_with_web_search.py` in operator-facing markdown.
- [ ] Unreachable relay probe in preflight (optional follow-up).
- [ ] `run_dir/effective-config.json` materialization on every allocate (partially documented elsewhere).
