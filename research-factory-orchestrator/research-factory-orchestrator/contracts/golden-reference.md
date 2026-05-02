# Telegram golden snapshots (D2)

## Purpose

Optional **`contracts/telegram-golden/`** directory holds a frozen `delivery-manifest.json` (and optional `allowlist-paths.txt`) for regression diffing of Telegram-shaped smoke runs.

## Capture procedure

1. Run a successful smoke with the target provider/interface, e.g.  
   `python3 -S scripts/rfo_v18_core.py smoke --runs-root /tmp/rfo-golden --provider telegram --interface telegram`
2. Copy `delivery-manifest.json` from the resolved `run_dir` into `contracts/telegram-golden/delivery-manifest.json`.
3. Add volatile dotted paths (e.g. `.run_id`, `.created_at`, `.attachments`) to `allowlist-paths.txt` one path per line (`#` comments allowed).

## Diff procedure

`python3 -S scripts/_diff_telegram_against_golden.py <run_dir>`

- If `contracts/telegram-golden/` is **missing** → exit **0** with skip JSON (skeleton only in v19.0.3).
- If golden exists → deep-compare against `run_dir/delivery-manifest.json` honoring allowlist.

## Promotion to release gate (v19.0.4)

**v19.0.4** will promote **D1** to **`must_ok`** after a frozen snapshot is committed and CI is wired to fail on unexpected drift.

## Golden refresh criteria

Refresh the golden snapshot **only** on intentional contract or smoke-output changes (document the reason in the release notes).
