# Phase 4 — Code hygiene (ruff / pyflakes / bandit / vulture / radon)

- ts: `20260508T012512Z`
- targets: `runtime/`, `scripts/`, `providers/`, `tools/`
- exclusions: `.venv/`, `.tmp-exec-runs/`, `__pycache__/`, `release-artifacts/`, `kb/`, `legacy/`
- python: 3.12.3
- venv: `_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/.venv/`

| tool      | version | exit | findings | artifact                                |
|-----------|---------|-----:|---------:|------------------------------------------|
| ruff      | 0.15.12 |    1 | **1207** | `05-hygiene/ruff.{json,txt}`             |
| pyflakes  | 3.4.0   |  123 |  **118** | `05-hygiene/pyflakes.txt`                |
| bandit    | 1.9.4   |    1 |  **154** | `05-hygiene/bandit.{json,txt}`           |
| vulture   | 2.16    |    3 | **1 (≥70)** / 77 (≥60) | `05-hygiene/vulture{,-60}.txt` |
| radon cc  | 6.0.1   |    0 | n/a (per-block scores) | `05-hygiene/radon-cc.{json,txt}` |
| radon mi  | 6.0.1   |    0 | 320 files (A=317, B=3, C=0) | `05-hygiene/radon-mi.txt` |

**Files scanned (Python):** 320 (`05-hygiene/_pyfiles.txt`).

---

## 4.1 ruff — 1207 findings

Top error codes:

| count | code | meaning                                          |
|-----:|------|--------------------------------------------------|
| 496  | E701 | multiple statements on one line (colon)          |
| 386  | E702 | multiple statements on one line (semicolon)      |
| 196  | E401 | multiple imports on one line                     |
| 101  | F401 | imported but unused                              |
|  10  | F841 | local variable assigned but never used           |
|   7  | E402 | module-level import not at top                   |
|   6  | F541 | f-string without placeholders                    |
|   4  | E741 | ambiguous variable name (`l`, `I`, `O`)          |
|   1  | E721 | use `is` / `isinstance` for type comparisons     |

**Interpretation.** ~88% of ruff findings (E701/E702/E401) are stylistic — many `scripts/validate_*.py` files are written in deliberate "compact" style with several statements per line. They are **noise** for an agent-native review and not bugs. Real bugs are:

- **F401 (101)** — dead imports, including `runtime/cli.py:5` (`sys`), `runtime/outbox_impl.py:11` (`runtime.util.sid`), `runtime/validators_core.py:2` (`json`), `runtime/work_units.py:15` (`json`).
- **F841 (10)** — dead local variables, e.g. `scripts/_smoke_v19_2_1_honesty.py:101,307` (`o`), `scripts/_test_mvr_profile_seed_only_disclosure.py:290` (`p_rt`).

Top files by ruff count: all are `scripts/validate_*` (compact-style validators, expected): `validate_job_lifecycle.py`(35), `validate_delivery_manifest_requires_ack.py`(34), `validate_skill.py`(31), `validate_outbox_delivery.py`(26), `validate_telegram_delivery.py`(25), …

## 4.2 pyflakes — 118 reported lines

Confirms the F401/F841 subset of ruff. No new categories beyond ruff. Top findings:

- 102 generic (mostly unused imports) — same set as ruff F401 / E401.
- 10 "local variable … is assigned to but never used" — same as ruff F841.
- 6 "f-string is missing placeholders" — same as ruff F541.

## 4.3 bandit — 154 findings

| severity | count |
|----------|------:|
| HIGH     |    3  |
| MEDIUM   |   24  |
| LOW      |  127  |

Top issue codes:

| count | code | check |
|-----:|------|-------|
| 48   | B603 | `subprocess` call without `shell=True` (low-risk pattern, but flag for input audit) |
| 31   | B404 | `import subprocess` (informational) |
| 20   | B101 | `assert` used (loses meaning in `python -O`) |
| 17   | B108 | hardcoded `/tmp/...` path |
| 13   | B110 | bare `try / except / pass` |
| 10   | B112 | bare `try / except / continue` |
|  7   | B310 | `urllib.request.urlopen` audit (file:// scheme allowed) |
|  4   | B105 | hardcoded password string (likely false positives — string constants like `"token"`) |
|  3   | B324 | weak SHA-1 hash (HIGH severity) |
|  1   | B607 | `start_process_with_partial_path` |

### HIGH severity (3) — must review

| file | line | issue |
|------|-----:|-------|
| `scripts/init_runtime.py` | 119 | `hashlib.sha1(...)` — pass `usedforsecurity=False` if non-crypto. |
| `scripts/interface_common.py` | 11 | same. |
| `scripts/match_io_methods.py` | 13 | same. |

These three are SHA-1 used for cache/identity hashes. Either annotate `usedforsecurity=False` or migrate to BLAKE2.

### MEDIUM severity in `runtime/` (1)

- `runtime/collector.py:67` — `urllib.request.urlopen` (`B310`). The collector is the **only HTTP egress in `runtime/`**, called when `RFO_EXTERNAL_COLLECTION` is enabled. Should be wrapped to reject anything but `https://` (and optionally `http://`), and have a network timeout enforced. This is also flagged in Phase 2 (agent-native concern: who decides which URLs?).

### MEDIUM severity in `scripts/` (23)

- `B310` (urllib): `scripts/run_rfo_full_research.py:48,75,91`, `scripts/run_rfo_with_web_search.py:65,89,105` — confirms Phase 2 finding that these scripts open arbitrary URLs (Wikipedia / SearXNG / Google / Bing search endpoints).
- `B108` (hardcoded `/tmp`): `scripts/_rfo_path_guard.py:155-158`, several `_smoke_*` scripts.
- `B108` `scripts/validate_no_local_paths_in_chat.py:12`, `scripts/validate_provider_payload.py:21`, `scripts/verify_openclaw_run.py:106` — paths used only as test fixtures; LOW operational risk.

### LOW severity in `runtime/` — full list

```
runtime/collector.py:67       [B310/MEDIUM]  urlopen audit
runtime/error_log.py:34       [B110/LOW]     try/except/pass
runtime/failure_impl.py:6     [B404/LOW]     import subprocess
runtime/failure_impl.py:70    [B603/LOW]     subprocess.run
runtime/failure_impl.py:92    [B603/LOW]     subprocess.run
runtime/outbox_impl.py:7      [B404/LOW]     import subprocess
runtime/outbox_impl.py:91     [B603/LOW]     subprocess.run
runtime/outbox_impl.py:185    [B110/LOW]     try/except/pass
runtime/outbox_impl.py:404    [B603/LOW]     subprocess.run
runtime/outbox_impl.py:413    [B110/LOW]     try/except/pass
runtime/output_filter.py:28   [B112/LOW]     try/except/continue
runtime/schema_defaults.py:138 [B110/LOW]    try/except/pass
runtime/smoke_impl.py:6       [B404/LOW]     import subprocess
runtime/smoke_impl.py:48      [B603/LOW]     subprocess.run
runtime/smoke_impl.py:61      [B603/LOW]     subprocess.run
runtime/util.py:19            [B110/LOW]     try/except/pass
runtime/validate_impl.py:6    [B404/LOW]     import subprocess
runtime/validate_impl.py:40   [B603/LOW]     subprocess.run
runtime/validate_impl.py:43   [B603/LOW]     subprocess.run
runtime/validate_impl.py:104  [B603/LOW]     subprocess.run
runtime/validate_impl.py:232  [B603/LOW]     subprocess.run
runtime/worker_impl.py:6      [B404/LOW]     import subprocess
runtime/worker_impl.py:298    [B110/LOW]     try/except/pass
runtime/worker_impl.py:345    [B603/LOW]     subprocess.run
runtime/worker_impl.py:443    [B110/LOW]     try/except/pass
```

The `try/except/pass` blocks (5×) are the most concerning class for runtime correctness: error swallowing in `outbox_impl.py:185,413`, `worker_impl.py:298,443`, `error_log.py:34`, `util.py:19`, `schema_defaults.py:138`. Each should be reviewed individually; logging-only swallows are acceptable, but truly silent ones can hide real failures.

The `subprocess.run` calls (10× in `outbox_impl`, `smoke_impl`, `validate_impl`, `worker_impl`, `failure_impl`) are LOW because they pass arg lists (no shell). They invoke external CLI tools — `git`, `python3`, validators — for legitimate orchestration, not user input.

## 4.4 vulture — dead-code candidates

At **min-confidence 70%** vulture finds **only 1** issue: `scripts/run_rfo_with_web_search.py:40` unused import `Optional`.

At **min-confidence 60%** (advisory) vulture finds **77** items distributed as: 33 unused attributes, 19 unused functions, 18 unused variables, 6 unused methods, 1 unused import.

`runtime/`-only signals at 60% (review individually — many are public API or registered via JSON contracts):

```
runtime/capability.py:44      unused function 'attenuate'
runtime/capability.py:59      unused function 'verify_token_file'
runtime/judge_panel.py:17     unused function 'run_position_swap_judges'
runtime/judge_panel.py:33     unused function 'write_single_model_ledger'
runtime/judge_panel.py:50     unused function 'write_ledger_stub'
runtime/merkle_anchor.py:21   unused function 'write_anchor'
runtime/output_filter.py:39   unused function 'filter_file'
runtime/publish_policy.py:9   unused function 'load_publish_policy'
runtime/slo.py:15             unused function 'compute_slis'
runtime/util.py:37            unused variable 'CLAIM_STATUS_LEGACY_ALIASES'
runtime/validators_core.py:85 unused function 'run_all'
runtime/work_units.py:42      unused method 'is_terminal'
runtime/work_units.py:46      unused method 'is_known'
runtime/work_units.py:52      unused variable 'WU_PENDING'
runtime/work_units.py:53      unused variable 'WU_RUNNING'
runtime/work_units.py:54      unused variable 'WU_TERMINAL'
```

These could be either: dead public exports kept for backward compat, or features wired only via JSON contracts (which static AST cannot see). Recommended action: cross-check against `runtime/capability.py`, `runtime/judge_panel.py`, etc. before deleting. **This is advisory, not blocking.**

## 4.5 radon — cyclomatic complexity & maintainability

### Cyclomatic complexity (top-25 by CC)

```
 128  F  runtime/outbox_impl.py:51                       cmd_outbox
  63  F  runtime/validate_impl.py:86                     validate
  63  F  scripts/run_core_validators.py:135              main
  62  F  scripts/validate_v19_fixture_suite.py:138       _check_advisory
  45  F  scripts/build_sacred_path_graph.py:22           main
  44  F  scripts/run_typed_grounding.py:60               main
  43  F  runtime/failure_impl.py:14                      cmd_failure
  39  E  scripts/validate_v19_fixture_suite.py:81        _check_expected
  39  E  scripts/validate_release_report.py:23           main
  39  E  scripts/validate_job_lifecycle.py:14            main
  38  E  scripts/validate_release.py:241                 main
  36  E  scripts/validate_v19_release_bad_suite.py:36    main
  35  E  scripts/validate_work_unit_completion.py:52     main
  34  E  scripts/validate_delivery_manifest_requires_ack.py:9   main
  34  E  scripts/run_core_validators.py:47               _advisory_judge_council
  33  E  scripts/validate_gate_semantics.py:11           main
  33  E  scripts/validate_chat_message_plan.py:11        main
  32  E  scripts/validate_seed_only_truth.py:53          main
  32  E  scripts/validate_delivery_manifest.py:7         main
  30  D  scripts/validate_outbox_event_semantics.py:15   main
  30  D  scripts/validate_error_log_quality.py:55        main
  29  D  scripts/validate_outbox_delivery.py:5           main
  27  D  runtime/render.py:76                            render_all
  26  D  scripts/validate_validator_coverage.py:98       main
  26  D  scripts/_smoke_v19_2_1_repro_baseline.py:68     main
```

Rank meaning (radon): `A` ≤5, `B` ≤10, `C` ≤20, `D` ≤30, `E` ≤40, **`F`** > 40 (very complex).

**Critical hot spots in `runtime/` (rank `F`):**

- `runtime/outbox_impl.py:51 cmd_outbox` — **CC=128**. By far the worst spot in the codebase. Single function controls outbox lifecycle (probably claim/lease/dispatch/retry/legacy-aliases). Strong refactor candidate.
- `runtime/validate_impl.py:86 validate` — **CC=63**. The umbrella entrypoint for all skill validators.
- `runtime/failure_impl.py:14 cmd_failure` — **CC=43**. Failure-handling dispatch.
- `runtime/render.py:76 render_all` — CC=27 (rank D).

### Maintainability index

| rank | files | meaning              |
|-----|-----:|----------------------|
| A   | 317  | very maintainable    |
| B   |   3  | moderate             |
| C   |   0  | low                  |

The 3 rank-`B` files are the worst:

```
MI=11.1  scripts/validate_v19_fixture_suite.py
MI=13.4  scripts/run_core_validators.py
MI=15.2  scripts/validate_logical_consistency.py
```

Worst rank-`A` files (still in `A` but bottom of the band):

```
MI=20.0  scripts/validate_release.py
MI=21.3  runtime/outbox_impl.py
MI=24.6  runtime/render.py
MI=24.8  scripts/_smoke_v19_2_integration.py
MI=25.4  runtime/worker_impl.py
MI=29.0  runtime/validate_impl.py
MI=29.1  runtime/failure_impl.py
```

Of `runtime/` modules: `outbox_impl.py`, `worker_impl.py`, `validate_impl.py`, `failure_impl.py`, `render.py` are the lowest-MI, which lines up exactly with the high-CC list.

## 4.6 Severity summary (Phase 4)

| layer | category | counts | notes |
|------|---------|--------|-------|
| `runtime/` | dead imports (F401) | 4 | `cli.py`, `outbox_impl.py`, `validators_core.py`, `work_units.py` |
| `runtime/` | bandit MEDIUM (B310 urlopen) | 1 | `collector.py:67` — only HTTP egress in runtime; needs scheme guard + timeout |
| `runtime/` | bandit LOW (B110 silent except/pass) | 5 | `error_log.py:34`, `util.py:19`, `outbox_impl.py:185,413`, `worker_impl.py:298,443`, `schema_defaults.py:138` |
| `runtime/` | high cyclomatic complexity (rank F, CC≥40) | 3 | `cmd_outbox` 128, `validate` 63, `cmd_failure` 43 |
| `runtime/` | low MI (rank A bottom) | 5 | `outbox_impl`, `worker_impl`, `validate_impl`, `failure_impl`, `render.py` |
| `scripts/` | bandit HIGH (SHA-1) | 3 | `init_runtime.py:119`, `interface_common.py:11`, `match_io_methods.py:13` |
| `scripts/` | bandit MEDIUM (B310 urlopen) | 6 | `run_rfo_full_research.py`, `run_rfo_with_web_search.py` (already flagged in Phase 2) |
| `scripts/` | rank B MI | 3 | `validate_v19_fixture_suite.py`, `run_core_validators.py`, `validate_logical_consistency.py` |
| any  | dead vars / functions (vulture ≥70) | 1 | `run_rfo_with_web_search.py:40` |

The top **agent-native** concerns surfaced in Phase 4 (in addition to Phase 2/3 hardcode):

1. `runtime/collector.py:67 urlopen` — confirms `urllib.request` is the only HTTP egress; missing scheme allow-list and explicit timeout.
2. `runtime/outbox_impl.py:51 cmd_outbox` — CC 128 with embedded subprocess calls (`B603` × 4) and silent excepts (`B110` × 2): this is the highest-leverage refactor target if outbox semantics change.
3. Silent `except: pass` in `runtime/` — 5 sites that can hide misroutes/dispatch failures.

Stylistic ruff noise (E701/E702/E401) and bandit B603/B404 (`subprocess` use) are LOW and not blocking; the codebase deliberately uses compact validator style and CLI invocations.

## 4.7 Artifacts

```
05-hygiene/
├── _pyfiles.txt          # 320 .py paths
├── ruff.json             # full ruff JSON
├── ruff.txt              # concise format with ANSI
├── ruff.stderr.txt       # empty
├── pyflakes.txt          # 118 lines
├── bandit.json           # full bandit JSON (245 KB)
├── bandit.txt            # bandit text report
├── bandit.stderr.txt     # bandit log
├── vulture.txt           # 1 finding @ 70% conf
├── vulture-60.txt        # 77 findings @ 60% conf (advisory)
├── radon-cc.json         # cyclomatic complexity (block-level)
├── radon-cc.txt          # human-readable, block-rank ≥B
└── radon-mi.txt          # maintainability index (320 files)
```
