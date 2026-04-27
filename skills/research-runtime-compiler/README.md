# research-runtime-compiler

Standalone meta-skill that compiles a user request into a runnable research runtime project.

## Why this is a compiler
This skill does not directly produce a final report by default. It compiles a runtime with contracts, state, queue, schemas, templates, and execution guardrails. The generated runtime performs actual research.

## Main outputs
- `MASTER-PROMPT.md`
- `runtime-contract.json`
- `session-state.md`
- `runtime-state.json`
- `queue.json` (when needed)
- `artifact-manifest.json`
- `tool-registry.json`
- `final-package-manifest.json`
- item artifacts in `items/*`
- logs in `logs/*`

## Usage
```bash
python scripts/compile_runtime.py       --request-file examples/example-military-bases.md       --project-dir examples/generated-military-bases-runtime       --output-formats html json       --queue-mode auto       --depth-level deep       --autonomy-mode full_auto
```

## Queue mode
Queue can come from explicit list, file, discovery, workspace scan, or auto mode. Runtime loops until queue completion or blocked stop condition.

## Fact-checking and citations
The runtime enforces claim registry + fact-check + citation locator + error audit before final output.

## Reliability hardening
Runtime uses finite state machine, stage preconditions/postconditions, loop guards, retries, watchdog, idempotent writes, resume protocol, and checkpoint validation.

## Resume after crash
Load `runtime-state.json`, `queue.json`, and item `stage-status.json` and continue from the last valid stage. Never silently reset unless force rebuild is explicitly enabled.

## Scripts
- `scripts/compile_runtime.py`
- `scripts/create_project_scaffold.py`
- `scripts/validate_schemas.py`
- `scripts/validate_artifacts.py`
- `scripts/generate_sample_runtime.py`
- `scripts/check_no_external_skill_refs.py`

## Validation
```bash
python scripts/validate_schemas.py
python scripts/check_no_external_skill_refs.py
python scripts/generate_sample_runtime.py
python scripts/validate_artifacts.py --project-dir examples/generated-military-bases-runtime
```

## Tests
See `tests/*.md` for golden regression cases and expected behavior.
