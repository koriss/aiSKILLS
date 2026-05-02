# Audit trail policy (v18.5+)

- **trace.jsonl** uses a hash chain: each line includes `prev_hash` (SHA-256 of the prior canonical line, genesis `0…0` for the first record) and `record_hash` (SHA-256 of the canonical record without `record_hash`). Tampering at any line breaks `validate_trace_hash_chain.py`.
- **handoffs/** stores phase envelopes with the same `prev_hash` discipline between files.
- **Merkle batches** (`runtime/merkle_anchor.py`) compute a rolling `root_hash` for optional external anchoring (RFC 9162, SCITT-style transparency logs).

Citations: OpenFang-style audit logs; Google Trillian; RFC 9162 §2.
