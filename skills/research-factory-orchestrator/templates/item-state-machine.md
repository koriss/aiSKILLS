# Item State Machine (per queue item)

## Happy path
```text
pending
→ running_discovery
→ running_research
→ sources_normalized
→ evidence_mapping
→ claims_extracting
→ running_draft
→ draft_ready
→ fact_check_running
→ citation_locator_running
→ error_audit_running
→ fixing_output
→ validating
→ evaluating
→ complete
```

## Failure / branch
- `failed_retryable`, `failed_blocked`, `paused`, `skipped_existing_valid`

## Forbidden
```text
draft_ready → complete
pending → complete
running_draft → complete
```

**Complete** requires: final artifact exists, fact-check, citation anchors for verified claims, error audit passed or documented, validation + evaluation per contract.
