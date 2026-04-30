# v16 Research and Architecture Summary

Version: `16.0.0-execution-integrity-lifecycle-hardening`

v16 hardens the full lifecycle:

```text
command → entrypoint → runtime status → work-units → workers → tools/search ledgers → provenance → claims → renderers → delivery → status/evals
```

New hardening:
- explicit `scripts/run_research_factory.py`;
- `entrypoint-proof.json`;
- `runtime-status.json`;
- `command-router-contract.json`;
- `entrypoint-contract.json`;
- validators for runtime entrypoint, command mapping, SKILL.md imitation, status-claim consistency;
- lifecycle failure-corpus cases.
