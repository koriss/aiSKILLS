# v19.2.0 Loop Iterations (opt-openclaw)

## Iteration 1
- Environment: `/opt/openclaw/skills/research-factory-orchestrator`
- Install path verified: `runtime/version.json` = `19.2.0`
- Command path smoke:
  - `python3 -S scripts/interface_runtime_adapter.py ...`
  - `python3 -S scripts/runtime_job_worker.py --execute-runtime`
  - `python3 -S scripts/outbox_delivery_worker.py`
- Run dir: `/opt/openclaw/data/workspace/rfo-v192-loop-runs/runs/loop_test_v19_2_0_20260506T182115`
- Independent verifier:
  - `python3 scripts/verify_openclaw_run.py --run-dir <run_dir>`
  - Result: no lie entries (`lies=[]`), artifact signal indicates `delivery_status=stub_delivered`, `real_external_delivery=false` (expected for local stub/cli path)

## Iteration 2 (profile+hardening matrix)
- Command: `python3 -S scripts/_smoke_v19_2_integration.py`
- Result: `passed=true`
- Covered checks: profile matrix (mvr/full-rigor/required), legacy-leak guards, profile/registry alignment, subprocess timeout guard, contract/policy guards.

## Iteration 3 (archived — messenger delivery smoke)
- **Removed from repo:** `_smoke_telegram_real_send.py` and in-tree Bot API adapters.
- Use host/gateway integration tests for any real channel send; this skill validates
  artifacts + `verify_openclaw_run.py` only.

## Notes
- Standalone loop runs typically remain `stub_delivered` / `real_external_delivery=false` when only local CLI adapters run.
- Honesty-diff path is captured by independent verifier output and retained as command-level evidence.
