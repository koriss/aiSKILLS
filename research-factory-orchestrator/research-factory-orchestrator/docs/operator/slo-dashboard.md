# SLO dashboard (v18.5.0)

Use `runtime/slo.compute_slis(run_dir)` after each run; compare against `contracts/slo-config.json`.

| SLI | Meaning |
|-----|---------|
| `validators_pass_rate` | `validation-transcript.status == pass` |
| `delivery_success_rate` | `delivery-manifest.delivery_status` in delivered / stub_delivered |
| `replay_determinism_rate` | Unique `event_id` lines in `events.jsonl` |
| `injection_attempts_blocked_rate` | Populate from `output_filter` rejections when wired |

Export JSON to Datadog / Prometheus via your CI wrapper.
