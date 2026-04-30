
# Shard Ledger Policy

`shard-ledger.json` tracks every work unit.

Each shard record must include:

- work_unit_id;
- status;
- attempts;
- artifacts;
- validator_status;
- coverage_closed;
- open_debt;
- merge_status;
- last_error.

No unmerged shard = required for final delivery.
