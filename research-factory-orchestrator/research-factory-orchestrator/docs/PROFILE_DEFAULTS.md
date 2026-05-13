# Run profile defaults (contract vs entrypoints)

Single reference for default profile strings across the repo.

| Location | Default / fallback | Notes |
|----------|-------------------|--------|
| `contracts/run-profiles.json` | `default_profile`: **`dossier`** | Production contract; legacy env/CLI names remap in `runtime.profiles.resolve`. |
| `runtime/profiles.py` | Internal default **`dossier`** (and legacy alias → dossier). | |
| `scripts/rfo_execute.py` | Same as bridge (delegates to `run_rfo_with_web_search.py`) | **Canonical** prod argv for relay+queue; prefer in slash/compose. |
| `scripts/run_rfo_with_web_search.py` | CLI `--profile` default **`dossier`** | Bridge implementation; sequential relay query expansion from `contracts/query-fanout-config.json`. |
| `scripts/run_core_validators.py` | `--profile` default **`dossier`** | Validator harness default; fixtures may still embed `mvr`/`full-rigor` in `run-profile.json`. |

**Rule of thumb:** operators and bridge runs default to **`dossier`**. `publish-policy.json` blocks user-visible publish when `collection-result.json` has `seed_only: true`.
