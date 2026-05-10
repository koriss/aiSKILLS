# v19.2.0 — Agent honesty methodology (WebSearch + unreliable LLMs)

When an LLM **writes the test oracle** and the **implementation** in one session,
errors correlate: the model may assert green paths that artifacts contradict.
Use this checklist before trusting any “PASS” narrative.

## Research-first (WebSearch discipline)

1. **Primary sources** — prefer vendor docs / RFCs / issue trackers over SEO blogs.
2. **Recency** — check last-updated dates; pin library versions in notes.
3. **Triangulation** — at least two independent sources for API semantics.
4. **Negative search** — explicitly search for deprecations and renamed endpoints.

## Runtime verification (must be machine-grounded)

1. Run `scripts/validate_release.py` (or the `REQUIRED_GATES` subset you are iterating).
2. Never accept “validate passed” without `release-validation-transcript.json` **rc**
   fields for each gate.
3. For **user-visible send** claims, require evidence from the **host** (gateway logs,
   channel IDs, HTTP traces). This skill does not ship messenger delivery code.
4. For coverage claims, require `collection-coverage-result.json` and
   `source_coverage_passed` alignment (see ADR-015).

## Loop protocol (max 3 iterations)

1. **Capture** — save model answer + `run_dir` snapshot path.
2. **Diff** — `python3 -S scripts/verify_skill_run_claims.py --run-dir <rd> --model-answer <text>`.
3. **Classify** — bucket failures: artifact drift vs validator drift vs prompt drift.
4. **Fix smallest** — one hypothesis per iteration; re-run the narrowest smoke first.

## Stop conditions

- `LIE-DETECTED` from `verify_skill_run_claims.py` → do not ship; reset prompt and rerun.
- Any `COVERAGE-GAP` from `validate_validator_coverage.py` → repair fixtures or
  downgrade index rows to honest `meta` severities with explicit `n/a` repros.
