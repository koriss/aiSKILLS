# Dynamic Queue Protocol

## Sources of queue (no hardcoded entities in core)
- User explicit list; external file; workspace scan; criteria-based discovery; search-assisted discovery; auto split by dimensions defined **in the user request** or `runtime-contract.json`.

## Item record
Must align with `queue-item.schema.json`: id, slug, status, priority, retry fields, `output_files` pointers.

## Non-stop
While `queue.json` has `pending` or `failed_retryable` (under retry policy), the executor continues without prompting “next?”
