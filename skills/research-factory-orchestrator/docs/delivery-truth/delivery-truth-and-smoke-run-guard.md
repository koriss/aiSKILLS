# v18.3.2 Delivery Truth / Smoke-Run / Manual-Fallback Guard

## Problem

Observed failure: the assistant claimed “HTML report attached” and “RFO completed analysis” while the generated HTML embedded proof showed:

```text
delivery_status = not_queued
final-answer-gate.passed = false
run mode = seed/smoke/internal scaffold
```

A later manual snippet-based synthesis was presented as if it were RFO output.

## Invariants

```text
Prepared != sent.
Rendered != delivered.
Smoke-run != research-run.
Snippet synthesis != factchecked report.
Manual fallback != RFO output.
Local path != attachment.
Final-answer-gate false != completed.
```

## User-visible delivery rule

Any phrase such as “attached”, “sent”, “delivered”, “resent”, or “во вложении” requires:

```text
delivery-manifest.delivery_status in sent/delivered
attachment-ledger required attachment ack present
provider file id/message id present when provider supports it
final-answer-gate.passed=true for completion claims
```

If proof is absent, the only allowed message is limitation-first:

```text
Report/content was prepared locally, but user-visible file delivery is not proven.
```

## Smoke/seed rule

If a run is `seed_only_smoke`, deterministic scaffold, or external search did not execute, the user-visible result must say that the RFO created a scaffold only. It cannot be described as full research.

## Manual fallback rule

Manual web search/synthesis after RFO failure is allowed only as a clearly labelled preliminary draft. It cannot be called RFO output unless the manual claims/sources are inserted into RFO ledgers and gates are rerun.
