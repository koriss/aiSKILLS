# Run profile defaults (contract vs entrypoints)

Single reference for default profile strings across the repo.

| Location | Default / fallback | Notes |
|----------|-------------------|--------|
| `contracts/run-profiles.json` | `default_profile`: **`mvr`** | Contract “baseline” when resolving names. |
| `runtime/profiles.py` | If profile JSON is unreadable, internal default **`mvr`**. | Defensive fallback only. |
| `scripts/run_rfo_with_web_search.py` | CLI `--profile` default **`live-bridge`** | Stricter bridge / relay path; operators override with `mvr` for lighter rigor. |
| `scripts/run_core_validators.py` | `--profile` default **`mvr`** | Fixture / validator harness baseline; not the relay bridge default. |

**Rule of thumb:** bridge runners default to **`live-bridge`**; offline validator runs default to **`mvr`**.
