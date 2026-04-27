# Test: no progress loop guard

**Input:** repeated tool failures or repeated queries with no new sources.

**Expected behavior:** `no_progress_steps` / loop guard triggers; mark `failed_retryable` or `failed_blocked` with reason; do not loop forever; watchdog/trace records stale repeats.

**Failure:** infinite retry; same query without backoff or state change.
