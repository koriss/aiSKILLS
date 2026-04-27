# Test: queue non-stop

**Input:** `REPORT_FACTORY` with multiple `pending` items and no `STOP` command.

**Expected behavior:** Process items in order; no "next item?" prompt while pending/retryable items remain; checkpoint on disk.

**Failure:** Stopping after one item; asking user to continue; idle while queue is pending.
