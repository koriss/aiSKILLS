# Scripts

- `init_runtime.py` — create internal runtime under `--project-dir` (contracts, state, queue, items, logs).
- `validate_schemas.py` — check every `../schemas/*.schema.json` for basic JSON Schema structure.
- `validate_runtime.py` — check required runtime files and JSON/HTML sanity.

## Examples

```bash
python3 init_runtime.py --project-dir /tmp/rf-task --title "Sample task"
python3 validate_schemas.py
python3 validate_runtime.py --project-dir /tmp/rf-task
```

Dependency: Python 3 standard library only.
