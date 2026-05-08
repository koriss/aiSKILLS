# Phase 1 — built-in skill validators

## Run matrix

13 self-validators planned. First pass surfaced an analyzer ergonomics issue: 5 validators need an explicit `path`/`skill_dir` argument and exit with code `2` when run with no argv. The second pass corrected this and the third validator (`validate_no_provider_hardcode_text`) was further re-run as a per-file batch (it only takes a single file as input).

| # | Validator | Exit | Notes |
|---|---|---|---|
| 1 | `validate_no_provider_hardcode_text` (with `.`) | 1 | `IsADirectoryError` → re-ran as **batch** below |
| 2 | `validate_provider_specific_logic_not_in_runtime` (with `.`) | 1 | **REAL FINDING** (see below) |
| 3 | `validate_no_external_kb_dependency` | 0 | OK |
| 4 | `validate_runtime_contract_current` | 1 | **REAL FINDING** — code `F340` |
| 5 | `validate_interface_adapter_contract` (with `.`) | 0 | OK |
| 6 | `validate_command_router_mapping` (with `.`) | 0 | OK |
| 7 | `validate_no_ambient_context_runtime_override` | 0 | OK |
| 8 | `validate_skill` | 1 | Polluted by `.venv/__pycache__` (Phase-0 byproduct), **see caveat** |
| 9 | `validate_skill_discovery_frontmatter` | 1 | **REAL FINDING** — `wrong_or_missing_metadata_version_v18_3_2` |
| 10 | `validate_canonical_package_layout` | SKIP | Requires `package_zip`; not applicable to working tree |
| 11 | `validate_code_hygiene` | 1 | False positive: 4 stderr lines all about `.venv/` symlinks |
| 12 | `validate_all_python_ast` | 0 | OK |
| 13 | `validate_no_pycache` | 1 | All 1236 entries inside `.venv/` (false positive from Phase-0 venv) |

Raw outputs in `02-self-validators/`. Summary table also in `02-self-validators-summary.tsv`.

## Critical findings

### F1.1 — runtime/ has telegram hardcode

`scripts/validate_no_provider_hardcode_text.py` is a per-file checker. Running it across `runtime/`, `scripts/`, `providers/`, `contracts/`, `policies/`, `playbooks/`, `validation-profiles/`, and the top-level `*.md` produced **10 fails out of 384 files**:

| Path | Patterns matched |
|---|---|
| `runtime/compatibility-matrix.json` | `sendMessage|sendDocument`, `TELEGRAM_[A-Z_]+` |
| `runtime/cli.py` | `TELEGRAM_[A-Z_]+` |
| `scripts/_smoke_v19_2_1_repro_after_fix.py` | `TELEGRAM_[A-Z_]+` |
| `scripts/_smoke_v19_2_1_honesty.py` | `TELEGRAM_[A-Z_]+` |
| `scripts/interface_runtime_adapter.py` | `api\.telegram\.org`, `TELEGRAM_[A-Z_]+` |
| `scripts/_rfo_path_guard.py` | `api\.telegram\.org`, `TELEGRAM_[A-Z_]+` |
| `AGENTS.md` | `api\.telegram\.org`, `TELEGRAM_[A-Z_]+` |
| `CHANGELOG.md` | `sendMessage|sendDocument` |
| `scripts/validate_no_provider_hardcode_text.py` | `sendMessage|sendDocument` (the validator's own regex literals) |
| `scripts/validate_provider_specific_logic_not_in_runtime.py` | `sendMessage|sendDocument` (same — validator's own regex) |

The **two `runtime/` hits** are the headline agent-native violation: anything in `runtime/` referring to a specific channel (Telegram) breaks the contract. `scripts/interface_runtime_adapter.py` and `scripts/_rfo_path_guard.py` are also damning because they live in the run-time hot path.

The two validator self-hits are noise (the file contains its own pattern literals).

`AGENTS.md` and `CHANGELOG.md` are doc-only — flag in `docs` bucket, not a code-path failure.

### F1.2 — provider-specific script in scripts/

`validate_provider_specific_logic_not_in_runtime` reports:

```
provider-specific script in scripts/: _diff_telegram_against_golden.py
```

A Telegram-named diff script lives in `scripts/`. Plan does not yet say to delete it; it is recorded as a finding for the priority list.

### F1.3 — runtime contract drift

`validate_runtime_contract_current` returns:

```json
{
  "status": "fail",
  "code": "F340",
  "message": "current runtime contract does not list init_runtime outputs"
}
```

The runtime contract on disk does not enumerate `init_runtime` outputs even though the runtime emits them. Real architectural inconsistency.

### F1.4 — skill discovery frontmatter version mismatch

```json
{
  "status": "fail",
  "validator": "validate_skill_discovery_frontmatter",
  "version": "18.3.2-delivery-truth-smoke-runtime-contract-hotfix",
  "errors": ["wrong_or_missing_metadata_version_v18_3_2"]
}
```

Discovery frontmatter is missing the v18.3.2 metadata stamp the validator expects (or carries a wrong one). The validator itself is a v18.3.2 hotfix, so the rule is older than the v19.3 skill body — likely a stale validator vs. evolved frontmatter contract.

## Validator caveats

- `validate_skill`, `validate_no_pycache`, `validate_code_hygiene`: all three trip on `.venv/` from Phase 0 (`__pycache__` and `*.pyc` inside site-packages, plus venv symlinks). Decision: keep `.venv/` for the rest of static analysis (remove cost > value), document the caveat, and re-evaluate these three only after the venv is excluded by the validator itself or removed pre-release.
- `validate_canonical_package_layout`: requires a release zip; no zip in the working tree, so it is intentionally skipped at this static-analysis layer.

## Tally

- **PASS (exit 0)**: 6 — `validate_no_external_kb_dependency`, `validate_interface_adapter_contract`, `validate_command_router_mapping`, `validate_no_ambient_context_runtime_override`, `validate_all_python_ast`, plus the second-pass green of two ergonomics fixes.
- **FAIL (exit 1)**: 6 — see findings above.
- **SKIP**: 1 — `validate_canonical_package_layout`.

Headline action items will roll up into Phase 6 along with Phase 2 (text-and-AST hardcode hunt) which will explore the same territory more broadly.
