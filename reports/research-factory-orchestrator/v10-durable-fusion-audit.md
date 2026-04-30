
# v10 Durable Fusion Audit

## Problems addressed

- Weak models fail on large tasks due to timeout/context overflow.
- Naive chunking causes skipped categories, local hallucinations, and lazy shard completion.
- v9 had stale version strings and privacy-gate leftovers.
- INT taxonomy could accidentally narrow retrieval if used as filter.

## v10 fixes

- durable work-unit contracts;
- shard-ledger;
- failure-packets;
- retry-ledger;
- resume-plan;
- watchdog-state;
- global merge artifacts;
- no unmerged shards final gate;
- INT coverage as expansion checklist;
- no fake INT claims;
- source provenance;
- all-source fusion map;
- dynamic package_skill.py;
- validate_skill.py updated for v10;
- stale v7/v8/v4 references cleaned from main skill validator path.

## Core rule

Chunking is allowed.
Completeness loss is not.

Each chunk must close a formal contract before merge.
Final report is generated only after global machine-readable merge.
