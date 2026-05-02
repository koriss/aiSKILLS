# D6 — Delivery truth core invariants (V6)

## Non-goals (clarification)

Delivery truth is **not** “more ceremony”. It is a **small, fail-closed** operational layer preventing user-visible lies about delivery and path leaks.

## Split delivery semantics (critical)

Manifest and gate MUST distinguish:

| Field | Meaning |
|-------|---------|
| `artifact_ready_claim_allowed` | Research outputs packaged locally / attached record exists |
| `external_delivery_claim_allowed` | User-visible channel (Telegram, webhook, …) proves delivery |
| `stub_delivery_disclosure_required` | If stub path used, explicit disclosure text required |
| `provider_adapter_completed` | Technical adapter finished (must **not** imply external) |

**Invariant:** `stub` may justify **`artifact_ready`** states, **never** `external_delivery_claim_allowed`.

## Minimum checks (V6)

1. **file_exists:** every artifact path in manifest exists on disk (or declared remote fetch succeeded — policy TBD).
2. **artifact_hash:** hashes match entries; strengthen beyond naive ACK string match (v18.5.0 lesson).
3. **provider_ack_or_explicit_stub:** ACK id present **or** `stub_delivery=true` with disclosure and `real_external_delivery=false`.
4. **ack_namespace:** matches provider (`cli:` local synthetic, `tg:msg:` telegram, `webhook:` …).
5. **provider_capability_snapshot:** frozen view of provider capabilities at validation time; `cli` ⇒ `real_external_delivery=false` **always**.
6. **external_delivery_claim_allowed:** true only with real external ack **or** explicit test hook flagged in manifest.
7. **no_local_path_leak:** scan **user_visible_artifacts** list (not only `chat/message-*.txt`): includes HTML/MD reports, `delivery-summary.json`, `verification-report.html`, telegram payloads, error snippets copied into chat.
   - Patterns: `/tmp/`, `/home/`, `/opt/`, `/var/`, `/usr/`, `/root/`, `~/`, Windows drive `^[A-Z]:\\`
8. **rollback explicitness:** On validation failure, write **failed** manifests even if optimistic files absent (`delivery-manifest.json`, `final-answer-gate.json`, `runtime-status.json` with `validation_failed`).

## KB safety (operational cross-cut)

- `kb_method_id` / `kb_source_id` must **never** satisfy `source_id` slot for factual evidentiary chain.
- Broken KB relations cannot support attribution edges (implementation enforces `lead_only` use).

## Release proof integrity (cross-reference)

Not strictly V6-only but **must** appear in release validation:

- No duplicate `run_id` posing as distinct steps (v18.5.1 dedupe lesson).
- Version drift: all proof `run.json` / `runtime-status.json` versions match release tag.
