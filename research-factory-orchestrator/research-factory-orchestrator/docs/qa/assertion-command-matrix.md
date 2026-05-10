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

**Canonical semver:** always read `skill_version` from `runtime/version.json`, not from duplicate headers alone.
