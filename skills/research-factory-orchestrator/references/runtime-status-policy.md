
# Runtime Status Policy

Progress must be rendered from `runtime-status.json` and `observability-events.jsonl`, not from model self-report.

If a text answer claims full pipeline/multi-agent/fanout, status must show work_units_total > 1 and workers_planned > 1.
