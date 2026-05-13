# ADR-022 — Relay reachability in preflight (no silent stub)

## Status

Accepted (2026-05-10)

## Context

`rfo-effective-config-v1` could show a resolved relay URL while TCP/HTTP to that
origin still failed (wrong IP after network change, SearXNG down, tun2proxy/DNS
issues). Operators and IDE agents then saw **exit 0 preflight** followed by a
long bridge run that returned **zero URLs** — easy to confuse with “RFO worked but
topic had no web hits”.

## Decision

1. After `build_effective_config_snapshot`, the bridge calls
   **`runtime.relay_reachability.merge_relay_probe_into_snapshot`**, which issues a
   minimal SearXNG-style **`/search?…&format=json`** via existing
   **`rfo_relay_search_helpers.relay_json_search`** (GET + POST fallback).
2. Success is defined as a parsed JSON payload with a **`results`** list
   (`result_count` present in relay meta). On failure, append **`relay_unreachable`**
   to `errors`, set **`blocked_dependency=web_search_json_api_base`**, force
   **`run_execution_mode=blocked_external_dependency`**, **`production_research=false`**.
3. **`RFO_SKIP_RELAY_PROBE=1`** skips the probe (unit tests / special harness only).
   **`RFO_PREFLIGHT_RELAY_TIMEOUT`** overrides the default **5.0** second budget.
4. **`scripts/rfo_execute.py`** sets **`RFO_EFFECTIVE_ENTRYPOINT=scripts/rfo_execute.py`**
   before loading the bridge so **`effective-config.entrypoint`** reflects the façade
   when operators use the public CLI.

## Consequences

- Preflight and full bridge start **fail closed (exit 2)** when the relay URL is
  syntactically valid but not a working JSON search endpoint.
- Native slash / gateway wiring must still pass a reachable base URL; this ADR
  does not change host-side argv — it only tightens **skill-side** honesty.

## References

- ADR-019 (single dossier funnel)
- `docs/plans/PLAN-rfo-agent-executable-single-behavior.md`
- `runtime/relay_reachability.py`
