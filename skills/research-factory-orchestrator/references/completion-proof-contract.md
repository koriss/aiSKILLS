
# Completion Proof Contract

`completion-proof.json` is mandatory.

No completion proof = no final delivery.

The model cannot claim stages, counts, files, gates, sources, claims, or citations unless they are represented in completion-proof with artifact paths and hashes.

Required structure:

```json
{
  "task_id": "",
  "item_id": "",
  "pipeline_version": "v12-report-delivery-system",
  "stage_count_required": 21,
  "stage_count_completed": 21,
  "artifacts": [],
  "validators": [],
  "counts": {},
  "final_delivery_allowed": false,
  "created_at": ""
}
```
