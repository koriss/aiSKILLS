
# Orchestrator-Worker Practice Policy

The orchestrator does not perform the entire research directly.

It must:
1. compile coverage axes;
2. create bounded work-units;
3. assign work-units to subagents or worker passes;
4. monitor timeouts and partial outputs;
5. retry or replace failed units;
6. synthesize only after quorum and coverage gates.

Subagents receive narrow contracts, not the full task dump.
