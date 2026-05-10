# v19.2.0 Loop Iterations (historical host snapshot)

> [!NOTE]
> Historical environment notes in this file are frozen for traceability. They are
> not canonical deployment paths for current host setups.

## Iteration 1
- Environment: `<host-skill-root>/research-factory-orchestrator` (historical snapshot used a host-specific `/opt/...` path)
- Install path verified: `runtime/version.json` = `19.2.0`
- Command path smoke:
  - `python3 -S scripts/interface_runtime_adapter.py ...`
  - `python3 -S scripts/runtime_job_worker.py --execute-runtime`
  - `python3 -S scripts/outbox_delivery_worker.py`
- Run dir: `<host-workspace>/rfo-v192-loop-runs/runs/loop_test_v19_2_0_20260506T182115`
- Independent verifier:
  - `python3 scripts/verify_skill_run_claims.py --run-dir <run_dir>`
  - Result: no lie entries (`lies=[]`), artifact signal indicates `delivery_status=stub_delivered`, `real_external_delivery=false` (expected for local stub/cli path)

## Iteration 2 (profile+hardening matrix)
- Command: `python3 -S scripts/_smoke_v19_2_integration.py`
- Result: `passed=true`
- Covered checks: profile matrix (mvr/full-rigor/required), legacy-leak guards, profile/registry alignment, subprocess timeout guard, contract/policy guards.

## Iteration 3 (archived — channel delivery smoke)
- **Removed from repo:** `_smoke_channel_real_send.py`-style in-tree channel/Bot API adapters.
- Use host/gateway integration tests for any real channel send; this skill validates
  artifacts + `verify_skill_run_claims.py` (compat wrapper: `verify_openclaw_run.py`) only.

## Notes
- Standalone loop runs typically remain `stub_delivered` / `real_external_delivery=false` when only local CLI adapters run.
- Honesty-diff path is captured by independent verifier output and retained as command-level evidence.
