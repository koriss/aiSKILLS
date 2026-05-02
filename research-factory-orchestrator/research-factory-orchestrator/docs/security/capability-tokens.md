# Capability tokens

Signed, expiring capability objects (`runtime/capability.py`) scope adapter actions (`deliver_external:<provider>`, `read_sources`, …). Each outbox event should persist `capability-tokens/CAP-<event_id>.json` for `validate_capability_scope.py`.

Mitigation mapping: **OWASP LLM08 Excessive Agency** — deny-by-default execution unless capability verifies.

References: ACP-CT-1.0 (arXiv:2603.18829), CapToken patterns, object-capability (OCap) discipline.
