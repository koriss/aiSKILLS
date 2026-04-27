# Execution Runbook (AUTO_COMPILE_AND_EXECUTE)

## Preconditions
- User goal is clear enough to assign a `task_id` and `PROJECT_DIR`.
- Execution mode is **not** `COMPILE_ONLY` unless user explicitly requested it.

## Phase A — Analyze (global: `received_request` → `analyzing_request`)
- Parse scope, outputs, risk, whether queue/factory is needed.
- Set `execution_mode` in runtime contract (default `AUTO_COMPILE_AND_EXECUTE`).

## Phase B — Compile ( `analyzing_request` → `compiling_runtime` → `runtime_compiled` )
- Write `runtime-contract.json`, `runtime-state.json`, `queue.json` (if needed), `artifact-manifest.json`, seed `tool-registry.json`.
- Create `items/<item_slug>/` directories and placeholder artifacts as per `init_runtime.py`.
- **Do not** present compile output as final. **Forbidden:** transition `runtime_compiled` → `delivered`.
- If `execution_mode` is **not** `COMPILE_ONLY`, **immediately** transition `runtime_compiled` → `executing_runtime` and continue (files are the compile artifact; the user still waits for research output).

## Phase C — Execute ( `runtime_compiled` → `executing_runtime` → … → `delivered` )
1. **Tool discovery** → update `tool-registry.json` (see `tool-discovery-protocol.md`).
2. **Queue** — load/build queue; if pending items exist, **do not** ask “continue?”
3. **Per item** — follow `item-state-machine.md`:
   - research → sources → evidence → claims → draft (`draft_ready`)
   - fact-check → citation locator → error audit → fix → validate → evaluation
4. **Checkpoint** after each major stage (files are source of truth).
5. **Final** — when global state `final_ready`, produce user-facing delivery using `final-delivery-template.md`.

## Postconditions
- `logs/trace.jsonl` and `logs/activity-history.html` updated for material steps.
- User receives research result, not only file paths.

## Stop conditions
User `STOP`/`PAUSE`/`CANCEL`, unrecoverable block, or queue empty and all items terminal.
