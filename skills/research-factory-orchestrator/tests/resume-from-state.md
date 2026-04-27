# Test: resume from state

**Input:** `runtime-state.json` and `queue.json` exist; some items `paused` or `failed_retryable` after a simulated crash.

**Expected behavior:** Mode `RESUME_RUNTIME` (or `EXECUTE_EXISTING_RUNTIME`); load disk state; do not reset completed work; do not overwrite locked finals without `force_rebuild` + user intent; continue from last valid stage.

**Failure:** full recompile from scratch; lost artifacts; `complete` downgraded to `pending` without reason.
