# Assertion → verification command matrix

Single place to map **documentation claims** to **commands** that prove or falsify them. Keep in sync with `docs/AUDIT-LEDGER.md` when adding rows.

| Assertion (what the docs claim) | Verification command / artifact |
|-----------------------------------|-----------------------------------|
| Skill tree is complete and scripts exist | `python3 -S scripts/validate_skill.py` (exit 0) |
| Optional scripts list matches repo | `required_scripts` in `scripts/validate_skill.py` vs `ls scripts/` |
| Failure corpus index / class coverage | `python3 -S scripts/rfo_runtime_core.py failure` (reads `failure-corpus/index.json`) |
| Full bad-sample harness (CI) | `python3 -S tests/run_failure_corpus.py` (shim to `scripts/run_failure_corpus_evals.py`) |
| Core V1–V6 chain on a run dir | `python3 -S scripts/run_core_validators.py --run-dir <run-dir> [--profile mvr]` |
| HTML / wiki citation invariants | `python3 -m unittest tests.test_report_html_citations` (module path as in repo) |
| Semver in prose matches runtime | Compare docs to `runtime/version.json` (`skill_version`, `failure_corpus_index_version`) |
| Release / smoke orchestration | `python3 -S scripts/validate_release.py` (when running full release contour) |
| Source packet persisted + `collection-result` path coherence | Inspect `collection-result.json` → `external_source_packet_path`; optional `sources/source-packet.json` under run-dir (bridge path) |
| Relay bridge staging E2E (stdout handoff only) | **Manual / staging** — `scripts/run_rfo_with_web_search.py` with live `RFO_WEB_SEARCH_JSON_API_BASE`; expect stderr progress, stdout single `__RFO_SKILL_AGENT_HANDOFF__=` line (see [ADR-018](../adr/ADR-018-bridge-handoff-contract-and-portable-paths.md)). |
| Core relay lease smoke | **Manual** — coordinated worker + bridge queue; playbook [§ Relay busy](./RFO-FULL-RESEARCH-PLAYBOOK.md#relay-busy--lease-races) |
| HTML citations + banner blocks | `python3 -m unittest tests.test_report_html_citations` |
| Capability excerpt in HTML/MD reports | Inspect generated `report/full-report.html` for `rfo-capabilities-truth` / embedded JSON IDs; verify matches `feature-truth-matrix.json` |
| Agent handoff bundle artifact | Presence of `agent-handoff/bundle-manifest.json` (`rfo-agent-handoff-bundle-v1`) after execute/relay finalize |
| Model/chat honesty vs artifacts | `python3 -S scripts/verify_skill_run_claims.py --run-dir <run-dir> [--model-answer "..."]` (JSON uses `validator_id` **verify_skill_run_claims**) |
| Vendor-neutral doc surface gate | `rg` command documented in `docs/qa/NEUTRALITY-SCAN.md` (allowed residuals only) |

**Canonical semver:** always read `skill_version` from `runtime/version.json`, not from duplicate headers alone.
