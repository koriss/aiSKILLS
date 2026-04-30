# Runtime Executor Protocol

## Entry
Global stage must transition `runtime_compiled` → `executing_runtime` before any user-facing “done”.

## Loop
For each queue item (or single item):
1. Set item stage to research/discovery as defined in item FSM.
2. Collect and **normalize** sources; write `sources.json` (and index if used).
3. Build `evidence-map` + evidence notes; **no** claim without prior evidence note for important facts.
4. Extract claims into `claims-registry.json`.
5. Produce `draft` (HTML or contract format) — state `draft_ready`. **Forbidden:** `draft_ready` → user `delivered`.
6. Run fact-check (`fact_check_running`) — update verification fields.
7. Run citation locator (`citation_locator_running`) — every verified claim needs anchor + URL/local ref.
8. Error audit (`error_audit_running`) — structural, logical, contract, link checks.
9. Fixing loop (`fixing_output`) until validation passes or blocked.
10. Evaluation scores; if under threshold, return to fix/validate.

## Trace
Append trace line per significant action; update `activity-history.html` summary.

## End
When all items terminal and validation passes: `final_ready` → format user delivery → `delivered`.
