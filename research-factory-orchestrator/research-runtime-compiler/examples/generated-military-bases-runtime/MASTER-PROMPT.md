# MASTER-PROMPT

Task type: queue_based_research
Complexity level: 3
Autonomy mode: full_auto
Queue mode: auto
Depth level: deep
Output formats: html, json

## Required execution flow
user request
→ compiler
→ generated runtime
→ source collection
→ normalized sources
→ evidence map
→ claims registry
→ draft
→ fact-check
→ citation locator
→ error audit
→ fix output
→ validation
→ final package

## Task launch protocol
- Reload MASTER-PROMPT.md, runtime-contract.json, session-state.md, runtime-state.json, queue.json, artifact-manifest.json at every major stage.
- State files on disk are source of truth.

## Dynamic queue discovery
- Use configured queue source; do not hardcode domain entities.

## Non-stop execution loop
while queue has pending or failed_retryable items:
    reload state
    run stage pipeline
    checkpoint
    continue

## Reliability hardening
Context is disposable. Files are memory. State machine is law. Draft is not final. No source, no claim. No validation, no checkpoint. Pending queue means no stop.

## Finite state machine
pending -> running_discovery -> running_research -> running_evidence_map -> running_claims_registry -> running_draft -> draft_ready -> running_fact_check -> running_citation_locator -> running_error_audit -> fixing_output -> validating -> evaluating -> complete

## Tool registry
- Detect capabilities and write tool-registry.json before first research stage.

## Source policy
- Tier sources and track provenance.

## Evidence and claim model
- Build evidence-map.json and claims-registry.json before finalization.

## Fact-check, citation locator, error audit
- Final output cannot bypass these stages.

## Evaluation rubric
- Enforce thresholds from runtime-contract.json.

## Security model
- Read-only by default. Sensitive actions require explicit approval.

## Definition of Done
- draft exists
- final exists
- fact-check exists
- citation locator with anchors exists
- error audit exists
- validation passes
- evaluation thresholds pass or gaps documented
