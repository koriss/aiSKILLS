# Assertion → verification command matrix

Single place to map **documentation claims** to **commands** that prove or falsify them. Keep in sync with `docs/AUDIT-LEDGER.md` when adding rows.

| Assertion (what the docs claim) | Verification command / artifact |
|-----------------------------------|-----------------------------------|
| Skill tree is complete and scripts exist | `python3 -S scripts/validate_skill.py` (exit 0) |
| Optional scripts list matches repo | `required_scripts` in `scripts/validate_skill.py` vs `ls scripts/` |
| Failure corpus index / class coverage | `python3 -S scripts/rfo_runtime_core.py failure` (reads `failure-corpus/index.json`) |
| Full bad-sample harness (CI) | `python3 -S tests/run_failure_corpus.py` (shim to `scripts/run_failure_corpus_evals.py`) |
| Core V1–V6 chain on a run dir | `python3 -S scripts/run_core_validators.py --run-dir <run-dir> [--profile dossier]` |
| HTML / wiki citation invariants | `python3 -m unittest tests.test_report_html_citations` (module path as in repo) |
| Semver in prose matches runtime | Compare docs to `runtime/version.json` (`skill_version`, `failure_corpus_index_version`) |
| Release / smoke orchestration | `python3 -S scripts/validate_release.py` (when running full release contour) |
| Source packet persisted + `collection-result` path coherence | Inspect `collection-result.json` → `external_source_packet_path`; optional `sources/source-packet.json` under run-dir (bridge path) |
| Relay bridge staging E2E (stdout handoff only) | **Manual / staging** — `scripts/rfo_execute.py` (or spelled-out `run_rfo_with_web_search.py`) with live `RFO_WEB_SEARCH_JSON_API_BASE`; expect stderr progress, stdout single `__RFO_SKILL_AGENT_HANDOFF__=` line (see [ADR-018](../adr/ADR-018-bridge-handoff-contract-and-portable-paths.md)). |
| Core relay lease smoke | **Manual** — coordinated worker + bridge queue; playbook [§ Relay busy](./RFO-FULL-RESEARCH-PLAYBOOK.md#relay-busy--lease-races) |
| HTML citations + banner blocks | `python3 -m unittest tests.test_report_html_citations` |
| Capability excerpt in HTML/MD reports | Inspect generated `report/full-report.html` for `rfo-capabilities-truth` / embedded JSON IDs; verify matches `feature-truth-matrix.json` |
| Agent handoff bundle artifact | Presence of `agent-handoff/bundle-manifest.json` (`rfo-agent-handoff-bundle-v1`) after execute/relay finalize |
| Model/chat honesty vs artifacts | `python3 -S scripts/verify_skill_run_claims.py --run-dir <run-dir> [--model-answer "..."]` (JSON uses `validator_id` **verify_skill_run_claims**) |
| Vendor-neutral doc surface gate | `rg` command documented in `docs/qa/NEUTRALITY-SCAN.md` (allowed residuals only) |
| Handoff parser robust to extra stdout lines | `python3 -m unittest tests.test_parse_handoff_stdout_reference` |
| `primary_text` usage policy documented | `docs/qa/MANIFEST-PRIMARY-TEXT-POLICY.md` present and referenced by delivery layer docs |
| Post-incident deep analysis (queue / profile / delivery) | `docs/qa/RFO-DEEP-ANALYSIS-2026-05.md` present; cross-checks ADR-016 boundary claims |
| Remediation backlog after deep analysis | `docs/qa/RFO-REMEDIATION-ROADMAP.md` lists workstreams A–E + rollback + acceptance |
| Worker lease triage & recovery | `docs/qa/RFO-QUEUE-LEASE-INCIDENT-RUNBOOK.md` (§0 five-minute triage) + env `RFO_WORKER_LEASE_STALE_SECONDS` |
| Truth contracts (state vs delivery vs evidence) | `docs/qa/RFO-TRUTH-CONTRACTS-ALIGNMENT.md` maps artifacts ↔ semantics |
| **Lease class:** stale lease / poison parking / token matches selected pending | Code review `runtime/worker_impl.py` (`cmd_worker`, `_unlink_stale_lease`, failure-meta); manual relay smoke [playbook § Relay busy](./RFO-FULL-RESEARCH-PLAYBOOK.md#relay-busy--lease-races) |
| **Bridge class:** best-effort handoff must not fire on incomplete worker artifacts | Run `scripts/rfo_execute.py` with `--best-effort-continue` on a deliberately broken worker run; expect **non-zero** exit when sanity gate fails (no `__RFO_SKILL_AGENT_HANDOFF__=`) |
| **Gate class:** `final-answer-gate` semantics vs delivery proof | `python3 -S scripts/validate_gate_semantics.py --run-dir <run-dir>` and `python3 -S scripts/validate_logical_consistency.py --run-dir <run-dir>`; cross-read `final-answer-gate.json` + `delivery-manifest.json` |
| **Drift class:** feature truth matrix vs validators / marketing | Diff `config/feature-truth-matrix.json` (or packaged path) vs `docs/qa/RFO-TRUTH-CONTRACTS-ALIGNMENT.md` §5; run `python3 -S scripts/verify_skill_run_claims.py --run-dir <run-dir>` |
| **MVR / evidence class:** seed-only must not read as “fully researched” | `verify_skill_run_claims.py` + inspect `collection-result.json` / source packet paths; profile preflight in [RFO-FULL-RESEARCH-PLAYBOOK.md](./RFO-FULL-RESEARCH-PLAYBOOK.md) |

**Canonical semver:** always read `skill_version` from `runtime/version.json`, not from duplicate headers alone.
