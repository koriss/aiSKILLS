# ADR-009 — Architectural lenses & shared vocabulary (G1)

## Status

Accepted — documentation-only (v19.0.3).

## Context

Multiple review passes mixed **policy**, **capability**, **execution path**, **atomic work**, and **deterministic proof** into one ambiguous vocabulary (“profile”, “bundle”, “validator”, “workflow”). That collapse causes recurring design drift and false equivalences (e.g. “profiles replace subagents”).

## Decision — five non-interchangeable layers

| Term | Meaning | Examples |
|------|---------|----------|
| **Profile** | Policy / caps / strictness | `mvr`, `full-rigor`, `propaganda-io`, `book-verification` |
| **Bundle** | Capability set packaged for reuse | research-core, propaganda-analysis |
| **Workflow** | Execution DAG / sequencing | acquire → evidence → validate → deliver |
| **Work-unit** | Atomic contract with required outputs / retry / merge | `WU-003` handoff envelope |
| **Validator** | Deterministic judge (no orchestration) | V1–V6 core validators |

**Profile ≠ Validator.** Profiles select policy; validators enforce proof. Neither is a substitute for orchestration.

## Six architectural lenses (for future ADRs)

1. **Reality Checker (default fail)** — promotion to “READY” requires explicit evidence (`NEEDS_WORK` default; see release `REQUIRED_GATES` / B4).
2. **Evidence Collector** — artifacts must be materialized where validators inspect (`rollback-stub.html`, manifests, transcripts).
3. **Orchestrator Quality Loop** — release transcript + fixture suites + smokes close the loop on regressions.
4. **Bundle / Workflow / Profile separation** — taxonomy above; no synonym drift without ADR revision.
5. **Plugin-safe surface** — contracts/schemas are the stable boundary; Python is implementation.
6. **Identity & Trust** — delivery claims split into explicit booleans; no silent `{}` rollback.

## Sources / attribution

Synthesized from internal **self-audit** plus external review themes (agency-agents “testing-reality-checker”, antigravity-awesome-skills bundle/workflow separation). This ADR is the **canonical vocabulary** for subsequent ADR-010+ documents.

## Roadmap

- **v19.0.4** — promote optional golden diff (`D1`) to `must_ok` after frozen snapshot; taxonomy drift automation follow-ups.
- **v19.1** — code-level bundle/workflow registry if needed (beyond vocabulary).
- **v20** — reserved for semver-major contract moves called out explicitly.

## Consequences

- Future ADRs **MUST** use this vocabulary or explicitly revise ADR-009.
- B4 release self-attestation references the **Reality Checker** lens.
