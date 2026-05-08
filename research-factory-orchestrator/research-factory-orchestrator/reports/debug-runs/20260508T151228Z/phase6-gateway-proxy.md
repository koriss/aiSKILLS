# Phase 6 gateway proxy

- File inspected: `/opt/openclaw/extensions/telegram/src/bot-native-commands.ts`
- Native parser `parseResearchFactoryOrchestratorMatch()` parses `--profile`, `--seed`, `--seeds`.
- Gateway execution path for `/research_factory_orchestrator` builds `execArgs`:
  - `python3 -S <adapterPath> execute --task <task> --runs-root <runsRoot>`
  - adds `--profile <profile>` when present
  - adds `--seed-urls <csv>` when seeds present
- This is argv proxy, not env proxy.
- Runtime side (`runtime/cli.py`) supports `execute --profile --seed-urls`, then `artifact_execute_impl` maps to runtime env/profile handling.

## Decision

No mismatch found in current path for native `/research_factory_orchestrator` command.
No code change required in phase 6.
