# Test: compile does not stop

**Input:** research request, default mode (no "compile only").

**Expected behavior:** After internal compile, global stage must advance to execution (`executing_runtime` or equivalent) and the agent must continue research, not return only with scaffold or prompt as the answer.

**Failure:** User is told to run the scaffold themselves; or global stage goes `runtime_compiled → delivered`.
