
# Contradiction Matrix

For contested topics, create `contradiction-matrix.json`.

Each entry:

```json
{
  "claim_id": "C001",
  "supporting_sources": ["S001"],
  "contradicting_sources": ["S002"],
  "resolution": "downgrade|disputed|prefer_primary|unresolved",
  "reason": ""
}
```

Contradictions must be represented in final report and chat summary unless immaterial.
