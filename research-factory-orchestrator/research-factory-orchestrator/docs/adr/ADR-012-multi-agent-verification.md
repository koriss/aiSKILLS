# ADR-012 — Multi-agent verification frontiers (v19.1)

## Status

Accepted — implemented in v19.1.0 (advisory channels only; **no seventh core validator**).

## Context

Core validators V1–V6 share the same artifacts and ordering. That symmetry enables confirmation bias: every stage sees the same hypothesis surface. Industry work on **deliberate asymmetry** (e.g. MARCH-style blinded checking), **typed grounding tiers** (GSAR-style partitions + non-suppression of contradictions), and **structured multi-judge consensus** (council / auditor patterns) shows measurable gains without replacing the primary gate graph.

## Decision

1. **A1 — Blinded checker (advisory)** — `scripts/run_blinded_checker.py` compares atomic signals derived from evidence against claim text without reading solver-authored narrative fields; output `validation/blinded-checker-report.json`; surfaced as `validation-transcript.advisory_channels.blinded_checker`. Inspired by deliberate information asymmetry in multi-agent verification literature (e.g. MARCH / blind-checker motifs).
2. **A2 — Typed grounding (advisory)** — `scripts/run_typed_grounding.py` computes GSAR-lite partitions `{grounded, ungrounded, contradicted, complementary}`, weighted `S`, and `decision_advisory` (`proceed` / `regenerate` / `replan`); **Property 5**: high-severity contradiction entries referencing missing `claim_id` inflate via `typed_groundedness_inflation` (non-suppression).
3. **A3 — Judge council contract (optional artifact)** — `schemas/core/judge-council.schema.json` + fixtures only; deterministic/heuristic judges in-repo; **no LLM judges** in runtime for v19.1.

Profiles may upgrade selected advisories to **block** only via explicit `blocking_rules` keys (documented per profile JSON).

## Relationship to ADR-009 lenses

These channels are **evidence / verification lenses** around the existing Reality Checker + Evidence Collector vocabulary — not a new orchestration tier. They attach to the same sacred path (`claim → evidence_card → source`) and preserve the **anti-ceremony** rule: six core validators, additive advisory scripts only.

## Consequences

- More JSON artifacts under `run_dir/validation/` on each v19 profile validate.
- Failure-corpus gains advisory/meta rows for observability codes (`BLIND-CHECK-MISMATCH`, `TYPED-GROUNDEDNESS-*`, `EXTERNAL-INSTRUCTION-SIGNAL`, `SOURCE-POLICY-UNKNOWN`).
- Future LLM-based judges belong in **dev/CI** harnesses, not silent expansion of `validators/core/`.
