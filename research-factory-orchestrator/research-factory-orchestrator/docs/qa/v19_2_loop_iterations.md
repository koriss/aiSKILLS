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
  - Result: no lie entries (`lies=[]`), artifact signal indicates `delivery_status=stub_delivered`, `real_external_delivery=false` (expected for local no-telegram-token path)

## Iteration 2 (profile+hardening matrix)
- Command: `python3 -S scripts/_smoke_v19_2_integration.py`
- Result: `passed=true`
- Covered checks: profile matrix (mvr/full-rigor/required), v18 leak guards, profile/registry alignment, subprocess timeout guard, contract/policy guards.

## Iteration 3 (telegram delivery contract)
- Command: `python3 -S scripts/_smoke_telegram_real_send.py`
- Result: `pass`
- Evidence: `http_hits=6`, `telegram_acks=6` (mock API trace proves non-stub provider path in test harness)

## Notes
- In this host environment, production Telegram delivery requires real bot token/chat route in runtime path; standalone loop run remained `stub_delivered` while dedicated real-send smoke with mock transport passed.
- Honesty-diff path is captured by independent verifier output and retained as command-level evidence.
