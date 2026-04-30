# Global State Machine

## States
```text
received_request
→ analyzing_request
→ compiling_runtime
→ runtime_compiled
→ executing_runtime
→ research_running
→ evidence_mapping
→ claims_extracting
→ draft_ready
→ fact_check_running
→ citation_locator_running
→ error_audit_running
→ fixing_output
→ validating
→ final_ready
→ delivered
```

## Forbidden transitions
```text
runtime_compiled → delivered
runtime_compiled → ask_user_to_run
draft_ready → delivered
compiling_runtime → delivered
fact_check_running → delivered
citation_locator_running → delivered
error_audit_running → delivered
```

## Notes
- `runtime_compiled` must always be followed by `executing_runtime` (or `blocked` with reason), never by `delivered`.
- `COMPILE_ONLY` mode may end at `runtime_compiled` **only** when user explicitly requested no execution; still document that research was not run.
