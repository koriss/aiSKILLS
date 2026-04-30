
# Timeout Recovery Policy

Timeout state machine:

```text
timeout detected
→ write failure-packet.json
→ inspect partial artifacts
→ shrink context packet
→ retry same work-unit
→ if failed, spawn replacement
→ if quorum still failed, mark partial/failed
```

A timed-out subagent cannot be counted as completed.
