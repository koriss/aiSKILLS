# ADR-019 — Single dossier funnel (no production lite profile)

## Status

Accepted (2026-05-10)

## Context

RFO historically exposed multiple run profiles (`mvr`, `live-bridge`, etc.) that allowed thinner evidence or scaffold-style paths. Product direction is **one** production conveyor: relay-backed **source packets**, richer HTML dossier artifacts, chat/Markdown as preview only.

## Decision

1. **`contracts/run-profiles.json`** exposes **`dossier`** as the only production profile (`default_profile: dossier`). Legacy CLI/env names remap to dossier inside `runtime.profiles.resolve`.
2. **Relay bridge** (`scripts/run_rfo_with_web_search.py`) runs **sequential relay query expansion** from templates in `contracts/query-fanout-config.json` (stable order; not a parallel multi-agent swarm), merges/deduplicates URLs, and records **`relay_query_fanout`** / **`query_vectors`** statistics on `collection-result.json`.
3. **Empty relay** outcomes always fail closed (exit ≠ 0); there is **no** user-facing path to proceed with empty relay via `mvr` or `RFO_ALLOW_MVR_EMPTY_RELAY`.
4. **ZIP packaging**: `worker_impl._build_package_allow_stub` is **only** true for explicit seed-only / artifact-only runs — not “live-bridge relaxed” stubs.
5. **Publish**: `contracts/publish-policy.json` gains `block_user_publish_when_collection_seed_only`; `decide_publish_allowed` rejects user-visible publish when `collection-result.json` has `seed_only: true` (wired from `runtime/outbox_impl.py`).
6. **Validation**: `live-bridge` validation JSON remains as a legacy filename-compatible overlay but matches dossier strictness.

## Consequences

- Operators must supply a working JSON relay; empty relay runs fail closed. Use **`--preflight`** on the bridge to emit **`rfo-effective-config-v1`** JSON without allocating a run-dir; canonical operator environments must **not** set smoke/experiment env keys (`RFO_SMOKE`, `RFO_EXPERIMENT_BRIDGE`, `RFO_ALLOW_LEGACY*`). Preflight also performs a **minimal JSON `/search` reachability probe** (ADR-022); unreachable relays are **`relay_unreachable`** + exit **2**, not a silent “successful” preflight.
- Fixture suites that still encode `mvr` run-profile JSON remain valid for **historical validator harness** rows; **new** runs record `dossier`.

## References

- ADR-016 (compute vs delivery split)
- ADR-022 (relay preflight reachability)
- `contracts/query-fanout-config.json`
