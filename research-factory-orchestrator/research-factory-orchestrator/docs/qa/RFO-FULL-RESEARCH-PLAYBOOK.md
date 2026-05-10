# RFO — full research playbook

Canonical operator knobs live in **`SKILL-core.md`** and **`docs/PROFILE_DEFAULTS.md`**; this playbook adds **routing**, **relay sequence**, **troubleshooting**, and **truth boundaries** without duplicating every env variable.

Related: [`RFO-CANONICAL-WORK-ROOTS`](./RFO-CANONICAL-WORK-ROOTS.md), [`assertion-command-matrix`](./assertion-command-matrix.md), [`RFO-MERGE-ANTI-REGRESSION`](./RFO-MERGE-ANTI-REGRESSION.md), ADRs **001**, **016**, **018**.

---

## §5.0 Golden path (three gates)

These are **logical** contours; naming of host commands varies by orchestrator.

### GH1 — `execute` (artifact-only synchronous)

One-shot compute that writes under `run_dir` and emits stdout handoff (ADR-016).

```bash
cd /path/to/research-factory-orchestrator   # inner package cwd
python3 -S scripts/interface_runtime_adapter.py execute \
  --runs-root "$RUNS_ROOT" \
  --task "$TASK"
```

### GH2 — Relay bridge (`run_rfo_with_web_search.py`)

Configurable JSON HTTP relay prefetch + collectors + finalize handoff (ADR-018). **Requires** `--web-search-json-api-base` or `RFO_WEB_SEARCH_JSON_API_BASE`.

```bash
export RFO_WEB_SEARCH_JSON_API_BASE="http://127.0.0.1:8180/search?q={query}&format=json"
python3 -S scripts/run_rfo_with_web_search.py \
  --runs-root "$RUNS_ROOT" \
  --task "$TASK"
```

Profiles: **`live-bridge`** (default stricter contour) vs **`mvr`** (minimal viable relay). Override with `--profile`.

### GH3 — Host invokes skill (conceptual)

The **external orchestrator** reads `result-manifest.json`, optional `marker.json`, and the stdout line prefixed `__RFO_SKILL_AGENT_HANDOFF__=`; it performs any user-visible send. The skill stays **compute-only**.

---

## Contents

1. [§5.0 Golden path](#50-golden-path-three-gates)
2. [Preflight](#preflight)
3. [Relay bridge — operational steps](#relay-bridge--operational-steps)
4. [`RFO_SOURCE_PACKET`](#rfosource_packet)
5. [`run_rfo_full_research` / presets](#run_rfo_full_research--presets)
6. [Packet vs work units](#packet-vs-work-units)
7. [Relay busy / lease races](#relay-busy--lease-races)
8. [Glossary — relay vs agent tools](#glossary--relay-vs-agent-tools)
9. [Source quality vs pipeline health](#source-quality-vs-pipeline-health)
10. [Track C — optional future work-unit bootstrap](#track-c--optional-future-work-unit-bootstrap)
11. [Troubleshooting](#troubleshooting)

---

## Preflight

```bash
cd /path/to/.../research-factory-orchestrator
python3 -S scripts/validate_skill.py    # exit 0
python3 -S scripts/run_rfo_with_web_search.py --help
python3 -S scripts/interface_runtime_adapter.py --help
```

Pick `RUNS_ROOT` on persistent storage approved by your ops policy (`/tmp` requires explicit consent flags — see verifier `verify_skill_run_claims`).

---

## Relay bridge — operational steps

Treat as **staging / operator** checklist (not CI-default). Cross-check timeouts and env names with `scripts/run_rfo_with_web_search.py --help`.

1. **Export relay base** — `export RFO_WEB_SEARCH_JSON_API_BASE=…` or pass `--web-search-json-api-base`.
2. **Choose profile** — default `live-bridge`; `mvr` for minimal smoke when profiles allow it.
3. **Runs root** — `--runs-root` points at durable workspace path.
4. **Task string** — non-empty `--task`; keep URL-heavy tasks quoted.
5. **Dry connectivity** — from the bridge host (not inside skill): `curl -sS -o /dev/null -w '%{http_code}\n' "$BASE"` or relay-specific ping.
6. **Start bridge run** — `python3 -S scripts/run_rfo_with_web_search.py …` (**stderr**: progress/`[DONE]`; **stdout**: handoff line only once finished).
7. **Locate `run_dir`** — newest directory under `$RUNS_ROOT` or derive from stdout manifest paths (host-specific).
8. **`collection-result.json`** — confirms collection phase bookkeeping; inspect `seed_only`, counts, relay errors.
9. **`sources/sources.json`** (or emitted path per run) — URL list + fetch metadata normalized toward `schemas/core/sources.schema.json` (failure records may appear in sibling diagnostics depending on normalization mode).
10. **`report/full-report.html`** — canonical dossier rendering; regenerate path via `ensure_canonical_full_report_html` if host tooling hints missing HTML.
11. **`feature-truth-matrix.json`** — validator-facing scaffolding; surfaced in HTML/MD excerpts (do **not** market as proof of messenger delivery).
12. **`delivery-manifest.json` + gates** — check `delivery_status`, stub flags vs errors.jsonl (ADR-016).
13. **`result-manifest.json` + capsule** — host reads artifacts paths; truncation in chat ≠ missing files on disk.
14. **`agent-handoff/bundle-manifest.json`** — prompts + key refs for downstream agent (bundle contract `rfo-agent-handoff-bundle-v1`).
15. **Honesty loop (optional)** — `python3 -S scripts/verify_skill_run_claims.py --run-dir "$RUN_DIR" --model-answer "$TEXT"`

---

## `RFO_SOURCE_PACKET`

JSON artifact listing **seed sources** consumed by collectors (verification mode + citation_scope per source). **Does not**, by itself, create `work-units.json` or queue rows; workers synthesize queues from explicit work-unit inputs or decomposition outputs in the canonical pipeline unless **Track C** (below) adopts a bridging policy.

Consult source packet builders in **`source_acquisition_broker`** / collector integration for field names active in **your** checkout (avoid citing line anchors as permanent contracts).

---

## `run_rfo_full_research` / presets

Treat **`run_rfo_full_research`** and **`RFO_EMBEDDED_PRESETS`** as **expert contours**. Before documenting a branch as recommended:

1. Open `scripts/run_rfo_full_research.py` (or successor) and confirm the branch executes on current tree.
2. If dead / experimental, label docs **secondary**; **happy path** stays GH2 relay or GH1 artifact execute unless maintainers advertise otherwise.

---

## Packet vs work units

Relay **GH2** forwards the packet early; **`cmd_run` / worker** create work-queue phases when **`work-units.json`** or **`decomposition.json`** exist **or** decomposition produces planned units — otherwise **`total_planned=0`** is an allowed intermediate state until **Track C**. This is **not** automatically “relay skipped work.”

---

## Relay busy / lease races

Symptom: bridge retries (“not claimed” / stale lease) while a **parallel worker** already consumed the allocation.

- **Lease truth** — inspect `runtime/queue`/lease artifacts relevant to worker profile.
- Diagnose contention vs infra failure (`ss`, worker logs).
- Prefer single-writer runs for smoke; scale-out only with explicit queue policy.

---

## Glossary — relay vs agent tools

- **RFO JSON relay** — HTTP JSON search/fetch facade (any compliant server). The bridge uses stdlib `urllib` / subprocess policy from your wrapper — not the same as “native agent web_search” unless the **host** wires that tool to hit the same endpoint.
- **Orchestrator tools** — LLM-exposed tools live in the **host** layer; RFO compute does not call them unless you build an explicit **relay wrapper** outside this package.

---

## Source quality vs pipeline health

**Topic quality** (e.g., sparse Reddit rows) is **not** the same as **pipeline failure**. HTTP 403/429 from a domain may be normal — operators adjust engines, mirrors, rate limits, headers. Do **not** equate `citation_grounding` warnings with “missing work-units” without reading `feature-truth-matrix.json` + collection transcript.

---

## Track C — optional future work-unit bootstrap

**impl-21** options (owner pick): (A) bridge synthesizes a single work unit after packet, (B) worker default when packet present but no JSON, (C) document-only until policy changes. **Today:** document **C** as allowed; do not silently mark “complete” when gates say otherwise.

---

## Troubleshooting

| Symptom | Checks |
|---------|--------|
| `Connection refused` to relay | `ss -tlnp` on relay host, `curl` base URL, firewall |
| Empty `sources` / `collection-result` anomalies | Collector logs, relay JSON shape, HEAD vs GET policy flags |
| `validate_skill` failure | Package `cwd`, stale partial checkout, compare `scripts/validate_skill.py` list |
| HTML missing wiki refs | `python3 -m unittest tests.test_report_html_citations`, rerun render step |
| Verifier lie classes | Run `scripts/verify_skill_run_claims.py`; inspect `delivery-manifest.json` + `runtime/errors.jsonl` |
| “Completed” vs stub | Read `delivery-manifest.json` gates, not prose in chat excerpts |
