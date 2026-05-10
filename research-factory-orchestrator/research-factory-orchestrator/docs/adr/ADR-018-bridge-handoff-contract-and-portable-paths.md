# ADR-018 — Relay bridge handoff stdout + portable skill layout gate

## Status

Accepted — documents behavior shipped with skill **19.3.1**.

## Context

1. The relay bridge **`scripts/run_rfo_with_web_search.py`** invokes collector/worker tooling and emits a host-facing handoff capsule. Mixed progress lines on stdout complicate gateways that assume a single machine-parseable line.
2. Development trees sometimes symlink or mount the skill at a basename other than **`research-factory-orchestrator`**, triggering **`scripts/_rfo_path_guard.py`** false positives despite safe absolute roots.

## Decision

### A. Stdout vs stderr on the relay bridge

- **stderr:** all progress banners, **`[DONE] …`** traces, normalization/diagnostic logs (`reports/relay-bridge-sources-diagnostics.json` sidecar unchanged).
- **stdout:** solely the **`emit_agent_skill_handoff`** capsule line prefixed **`__RFO_SKILL_AGENT_HANDOFF__=`**, matching **`runtime/artifact_execute_impl.py`** `HANDOFF_STDOUT_PREFIX` (canonical contract with ADR-016).
- Packaging after bridge render MAY call **`build_package(..., quiet=True)`** so no auxiliary JSON blobs appear on stdout.

### B. Portable / non-canonical layout opt-in

- **`RFO_ALLOW_NON_CANONICAL_SKILL_LAYOUT=1`** relaxes basename/parent-dir checks in **`scripts/_rfo_path_guard.py`** only; forbidden path substring rules remain enforced.
- Operators symlink/mount at their own risk; production deploy should still prefer the canonical **`…/skills/research-factory-orchestrator/`** tree.

### C. Source packet persistence

- After bridge ingestion, **`collection-result.json`** field **`external_source_packet_path`** points to **`sources/external-source-packet.bridge.json`** relative to **`run_dir`** when the normalized packet was written.

## Consequences

- Host parsers SHOULD locate the marker by scanning stdout lines for **`HANDOFF_STDOUT_PREFIX`**, not by assuming no other stdout in dev/smoke wrappers. See **[ADR-019](./ADR-019-host-handoff-stdout-scanning.md)** for consolidated upstream guidance.
- ADR-016 unchanged in core split; see **ADR-016** MUST for execute path; **ADR-018** extends relay bridge symmetry.
