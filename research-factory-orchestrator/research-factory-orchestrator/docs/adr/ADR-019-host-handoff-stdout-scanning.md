# ADR-019 — Host parsing of stdout handoff lines

## Status

Proposed guidance for **orchestrator / gateway implementations outside this package**.

## Context

ADR-016 and ADR-018 require a single stdout line prefixed `__RFO_SKILL_AGENT_HANDOFF__=` (`HANDOFF_STDOUT_PREFIX`). Operators sometimes wrap the bridge or `execute` in scripts that emit additional stdout (smoke helpers, misplaced logging).

## Decision

Hosts that ingest the handoff SHOULD:

1. Scan **all non-empty lines** of stdout (typically **last matching line** suffices) for a line **starting with** `HANDOFF_STDOUT_PREFIX`.
2. **Not** assume the marker is exclusively the **final** line of the process unless their wrapper guarantees that invariant.

Implementing this behavior belongs in the **host** repository or gateway; the skill tree documents the contract only.

## Consequences

- Robust delivery even when thin wrappers print extra stdout before exit.
- Slightly more parsing logic on the host than “read last line only”.

## Optional manifest primary text

If a host chooses to treat `result-manifest.json` primary text as authoritative for a short user-visible summary, that is an **upstream** product decision and must stay aligned with `schemas/skill-result.schema.json` and audit policy — not implied by this ADR.
