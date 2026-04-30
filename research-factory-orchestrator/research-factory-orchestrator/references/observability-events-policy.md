
# Observability Events Policy

Trace logs must use structured events, not narrative diary text.

Example:

```json
{
  "event_name": "rfo.subagent.timeout",
  "run_id": "...",
  "work_unit_id": "WU-004",
  "subagent_id": "SA-004",
  "duration_ms": 300000,
  "partial_artifacts": ["claims-registry.json"],
  "next_action": "retry_or_replace"
}
```
