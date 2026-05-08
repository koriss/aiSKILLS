# Scripts

- `validate_skill.py` validates strict OpenClaw frontmatter and no-lightweight guardrails.
- `validate_schemas.py <schemas_dir>` validates schema JSON. Example: `python3 -S scripts/validate_schemas.py schemas`.
- `init_runtime.py --project-dir <run_dir> --task "..."` creates the current v19 runtime skeleton.
- `validate_runtime.py <run_dir>` validates mandatory runtime artifacts for the current runtime layout.
- `package_skill.py` creates `.skill` and workspace zip packages.
- `validate_package.py` checks package safety.

## Runtime note

Smoke/failure harness output must not be used as production acceptance evidence; use delivery/run-mode/final gates.
