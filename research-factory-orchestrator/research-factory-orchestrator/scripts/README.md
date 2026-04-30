# Scripts

- `validate_skill.py` validates strict OpenClaw frontmatter and no-lightweight guardrails.
- `validate_schemas.py <schemas_dir>` validates schema JSON. Example: `python3 -S scripts/validate_schemas.py schemas`.
- `init_runtime.py --project-dir <run_dir> --task "..."` creates the current v18 runtime skeleton.
- `validate_runtime.py <run_dir> [--profile current|legacy]` validates mandatory runtime artifacts. Default is `current`, matching `init_runtime.py`.
- `package_skill.py` creates `.skill` and workspace zip packages.
- `validate_package.py` checks package safety.

## v18.3.2 note

`validate_runtime.py` no longer requires the legacy `items/_template/*` skeleton unless explicitly called with `--profile legacy`.
Smoke/failure harness output must not be used as production acceptance evidence; use delivery/run-mode/final gates.
