# research-factory-orchestrator

Standalone **execution** skill with an **internal compiler**. Default behavior is **`AUTO_COMPILE_AND_EXECUTE`**: for a research request, the agent compiles a task-specific runtime (contracts, state, queue, artifacts), then **immediately runs** that runtime and delivers a **finished research result**—not a prompt pack or a “run this yourself” scaffold.

## When this is not the default
Only if the user explicitly asks for: `compile only`, `scaffold only`, `generate prompt only`, `do not run`. Then use `COMPILE_ONLY` and return artifacts; still do not abandon security or FSM rules.

## Layers
1. **Internal compiler** — produces `runtime-contract.json`, `runtime-state.json`, `queue.json`, `artifact-manifest.json`, `tool-registry.json`, per-item files under `items/`, and `logs/`.
2. **Runtime executor** — discovers tools, ingests sources, evidence map, claims, draft, fact-check, citation locator, error audit, fix, validate, deliver.

## Quick start (agent)
1. Choose execution mode (default: `AUTO_COMPILE_AND_EXECUTE`).
2. Pick `PROJECT_DIR` (workspace subdirectory, e.g. `.research-factory/<task_id>/`).
3. Run `python -S scripts/init_runtime.py --project-dir <PROJECT_DIR> --task-id <id>` to materialize the tree, then follow `templates/execution-runbook.md` in chat until `delivered`.
4. Use `python -S scripts/validate_schemas.py` and `python -S scripts/validate_runtime.py --project-dir <PROJECT_DIR>` before claiming checkpoint.

## User-facing output
Ship: executive summary, main findings, evidence-backed analysis, claim verification table, citations with anchors, limitations, and paths to any written files. Internal JSON/HTML under `PROJECT_DIR` are support evidence, not the main answer by themselves.

## Scripts
- `init_runtime.py` — scaffold + minimal valid JSON seeds.
- `validate_runtime.py` — required files, JSON parse, basic HTML.
- `validate_schemas.py` — all `schemas/*.schema.json` structurally valid.

## Files
See `SKILL.md` for full state machines, security, and rubric.
