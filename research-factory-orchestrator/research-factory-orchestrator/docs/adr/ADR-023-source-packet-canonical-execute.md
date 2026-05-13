# ADR-023 — Source-packet canonical execute vs relay bridge

## Status

Accepted (PR-0 feasibility + PR-1 vertical slice complete in-repo).

## Context

RFO historically was **relay-first**: `run_rfo_with_web_search.py` performs JSON relay prefetch, builds `research-plan.json`, and drives the adapter/worker pipeline. Operators and hosts risked a **hybrid**: a “source-packet” JSON on disk while machine artifacts still carried **relay runtime** semantics (`web_search_json_api_base`, `relay_source`, …).

## Decision

1. **One data contract** for agent-assembled evidence: `contracts/source-packet-v1.schema.json`.
2. **Two transports** for that contract (not two canons):
   - **Local single-agent:** `<skill_root>/.rfo-state/input/source-packet.json` + `python3 -S scripts/rfo_execute.py --runs-root <abs>`.
   - **Concurrent host:** `python3 -S scripts/rfo_execute.py --runs-root <abs> --source-packet <unique_path>`.
3. **`rfo_execute.py`** is the **canonical execute** for the packet path: argv **pre-scan** rejects legacy relay flags with `RFO_CONTRACT_CHANGED_SOURCE_PACKET_REQUIRED` (exit **2**); missing default packet → `RFO_INPUT_SOURCE_PACKET_MISSING`; stale packet guard via `RFO_STALE_PACKET_MAX_HOURS` / `--allow-stale-packet`; **no auto-creation** of packets inside execute.
4. **Relay prefetch + preflight** remain on **`scripts/run_rfo_with_web_search.py`** until a later phase removes them; they are **not** deleted in PR-0/PR-1.
5. **Agent collection provenance** (e.g. `"collection_methods": ["web_search"]`) is **allowed** in the packet and collection results. **Forbidden** in effective-config v2 and other machine JSON are **RFO relay runtime** fields (see `scripts/assert_no_relay_semantics.py` key list). *Agent-attested retrieval* ≠ *relay backend configuration*.
6. **Slash / native handler** does not live in this repo: the **host** assembles evidence, writes the packet (or invokes the relay bridge), then calls the appropriate script. The packet does **not** define the full gateway implementation.

## Consequences

- Host integrations must choose **packet execute** vs **relay bridge** explicitly; documentation lists both in `docs/runtime-paths.md`.
- `contracts/rfo-effective-config-v2.schema.json` describes packet-only runs (`search_mode: agent_supplied_packet`).
- `contracts/supported-skill-actions-v2.json` records `breaking_since` / `removed_invocations` for entrypoint drift; v1 contract remains for tooling mirrors with updated examples.

## PR-0 failure decision tree (summary)

| Branch | Condition | Next step |
|--------|-----------|-----------|
| **A** | Worker needs only `collection-result` **shape**, not relay backend | Adapter without relay semantics; iterate PR-0. |
| **B** | Worker **semantically** needs relay prefetch | Defer packet migration; extract worker core from relay bridge first. |
| **C** | Keep public relay CLI as “canon” **and** ship source-packet as parallel canon | **Forbidden** — hybrid operator confusion. |

## assert_no_relay (machine vs text)

- **Strict JSON:** forbidden keys and shapes are enforced in `scripts/assert_no_relay_semantics.py` (relay runtime: e.g. non-empty `web_search_json_api_base`, `relay_source` other than `none_agent_supplied_packet`, `relay_prefetch_bridge: true`, non-trivial `relay_chain`, …). **Allowed:** `collection_methods` values like `web_search` (agent collection provenance).
- **Soft text:** optional `--soft-text` scan of `report/` and `chat/` for relay-shaped prose heuristics.

## Roadmap: Phases A–G (post PR-0/PR-1)

| Phase | Scope | In-repo status (summary) |
|-------|--------|---------------------------|
| **A** | argv hard-stop legacy public relay flags on packet entrypoint; migration messaging | **A (packet):** pre-scan in `rfo_execute.py`. **A (bridge):** unchanged; full removal of relay CLI deferred. |
| **B** | Writable `.rfo-state` skill root; no silent fallback | Default packet path documented; execute refuses missing packet. |
| **C** | Schema + `collection_integrity` + marketing grep + snippet postrun | Bootstrap merge in `runtime/source_packet_run.py`; `validate_operator_facing_markdown.py`. |
| **D** | Execute + adapter; two transports | `rfo_execute.py`, `runtime/source_packet_run.py`, `docs/runtime-paths.md`. |
| **E** | effective-config v2 + supported-skill-actions-v2 | Contracts + `assert_no_relay_semantics.py`. |
| **F** | User-facing summary JSON + prompt-template passes | Incremental follow-up (rg-driven prompt edits); not a PR-1 gate. |
| **G** | Postrun limitations / `final_verdict_allowed` from snippet mix | Merged in `source_packet_run` for bootstrap profile. |
