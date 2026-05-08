# Phase 0 — tooling

## Decision

System has no `ruff`/`pyflakes`/`pylint`/`bandit`/`vulture`/`radon`. The skill has no `pyproject.toml`/`requirements-dev.txt`. We installed analyzers into an isolated venv inside the skill directory:

`/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator/.venv/`

`.gitignore` already excludes `.venv/` (lines 6–7), so the venv will not leak into git history.

## Environment

- Python: `3.12.3` (system `/usr/bin/python3`)
- Pip: `24.0`

## Installed analyzers

| Tool | Version | Used in |
|---|---|---|
| ruff | 0.15.12 | Phase 4 (lint, codestyle, common antipatterns) |
| pyflakes | 3.4.0 | Phase 4 (cross-check edge cases) |
| bandit | 1.9.4 | Phase 4 (security: SSRF, eval, hardcoded creds) |
| vulture | 2.16 | Phase 4 (dead code) |
| radon | 6.0.1 | Phase 4 (cyclomatic complexity, maintainability index) |

Full pip freeze: `01-tooling-pip-freeze.txt`.

## Invocation pattern (used in subsequent phases)

```bash
SKILL_DIR=/home/kazak/_projects/aiSKILLS/research-factory-orchestrator/research-factory-orchestrator
cd "$SKILL_DIR"
.venv/bin/ruff check ...
.venv/bin/bandit -r ...
```

No analyzers were run during Phase 0; only installed and version-pinned for reproducibility.
