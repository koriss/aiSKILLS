# Delivery manifest golden snapshots (archived procedure)

## Status

The optional **`contracts/telegram-golden/`** directory and the diff helper
**`scripts/_diff_telegram_against_golden.py`** were removed from the tree.
Older release notes may still mention them; do not follow those steps.

## Current practice

- Regression and honesty checks use **`scripts/verify_skill_run_claims.py`** (`validator_id`; legacy wrapper `verify_openclaw_run.py`) and the
  validator stack referenced from **`contracts/validator-registry.json`**.
- Default enqueue path is **`--interface cli --provider cli`**; user-visible
  delivery is outside this repository (see **`docs/adr/ADR-015-runtime-truth-restoration.md`**).

## If you need a frozen `delivery-manifest.json`

1. Run a smoke or full pipeline that produces a `run_dir` you trust.
2. Copy `run_dir/delivery-manifest.json` to a **private** fixture location
   (team process), not necessarily under `contracts/`.
3. Document volatile keys (timestamps, ids) in your own allowlist; there is
   no built-in deep-diff step in CI for Telegram-shaped manifests anymore.
