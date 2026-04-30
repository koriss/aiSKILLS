# Stage Record Contract

Every mandatory stage writes a record.

A stage record must contain:
- stage_name
- status: complete | blocked | failed
- started_at
- completed_at
- actions_attempted
- artifacts_created
- evidence_found
- blockers
- confidence_impact
- next_safe_action

No stage may be silently skipped.
