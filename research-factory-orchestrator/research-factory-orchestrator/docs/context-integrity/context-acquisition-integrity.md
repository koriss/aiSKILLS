# Context Acquisition Integrity Layer

## Purpose

This layer prevents a recurring OpenClaw/RFO failure mode:

```text
assistant says “I read everything”
→ only SKILL.md/core scripts were inspected
→ smoke-test or summary is presented as proof
→ subagent timeout is ignored
→ user receives false readiness/completion claim
```

This is not a style problem. It is a runtime integrity problem. RFO must treat context acquisition as a verifiable workflow with manifests, ledgers, and gates.

## Core distinction

The following operations are different and must not be conflated:

```text
READ:
  a file was opened and its content was inspected.

INDEX:
  a file was listed, hashed, and made retrievable, but not necessarily read into active context.

LOAD:
  file content was placed into the active reasoning context of the current turn/run.

EXECUTE:
  a script or runtime path was run.

SMOKE:
  a deterministic test runtime was executed. This proves only that the smoke path works.

MEMORY_WRITE:
  a note was written to persistent/local memory. This is not active context.
```

## Forbidden claims without proof

```text
“I read all files”
“I loaded the whole skill into context”
“I know the skill completely”
“the subagent read all files”
“smoke-test loaded everything into context”
“memory update means I now know everything”
```

These claims require mechanical evidence:

```text
read-ledger.jsonl
active-context-manifest.json
context-budget-analysis.json
context-claim-gate.json
subagent completion ack
```

## Allowed claims

```text
Operational core loaded.
Full workspace indexed.
Full workspace inventory/hash coverage built.
Specific files read on demand.
Smoke-test passed for runtime path.
Full exhaustive read not attempted / not completed.
```

## Modes

### operational_load

Loads only the operational core into active context:

```text
SKILL.md
entrypoint scripts
core runtime scripts
contracts
schemas
validator DAG
delivery/outbox contracts
failure-class index
```

The full workspace may be indexed but is not claimed as fully loaded.

### exhaustive_audit

Builds a complete file inventory and read-ledger in resumable batches. This may exceed active context, so the correct claim is read/index coverage, not active raw context.

### on_demand

Indexes the workspace and reads files only when a specific task requires them. This is the preferred long-term mode for large skills and KB-heavy packages.

## Required runtime artifacts

```text
context/context-load-request.json
context/file-inventory.json
context/context-budget-analysis.json
context/read-ledger.jsonl
context/read-coverage.json
context/active-context-manifest.json
context/indexed-context-manifest.json
context/context-load-limitations.json
context/context-claim-gate.json
```

## Gates

`context-claim-gate.json` must block false claims when proof is absent.

Example fail:

```json
{
  "status": "fail",
  "forbidden_claims": ["I read all files"],
  "read_coverage": {"total_files": 673, "files_opened": 17},
  "reason": "no read-ledger coverage for all files"
}
```

Example pass-with-limitations:

```json
{
  "status": "pass_with_limitations",
  "allowed_claims": ["operational core loaded", "workspace indexed"],
  "forbidden_claims": ["full active context loaded"]
}
```

## Failure classes

```text
F270 claimed_full_context_load_without_context_manifest
F271 claimed_all_files_read_without_read_ledger
F272 summary_or_inventory_presented_as_full_read
F273 smoke_test_presented_as_context_load
F274 subagent_started_presented_as_subagent_completed
F275 subagent_timeout_ignored_in_read_claim
F276 memory_write_presented_as_active_context
F277 impossible_context_request_accepted_without_limitation
F278 active_context_capacity_not_checked
F279 stale_version_claimed_after_newer_release_available
F280 path/name_confusion_in_skill_discovery
F281 readiness_claim_after_incomplete_read
F282 repeated_self_certification_after_user_correction
F283 debug_reasoning_leaked_to_user_chat
F284 user_requested_operational_loading_but_agent_generated_summary
F285 full_skill_understanding_claim_without_validator_or_inventory
F286 all_files_claim_uses_sampled_or_key_files_only
F287 context_load_no_file_hashes
F288 context_load_no_token_budget
F289 context_claim_not_reflected_in_final_gate
```

## Chat/provider rule

User-facing chat payload must not include hidden deliberation or scratchpad text. The following tokens are suspicious outside explicit debug artifacts:

```text
Reasoning:
Thought:
Chain of thought
scratchpad
internal deliberation
```

The provider renderer must strip or block them unless explicit debug mode is enabled and the output is routed to internal artifacts, not user chat.
