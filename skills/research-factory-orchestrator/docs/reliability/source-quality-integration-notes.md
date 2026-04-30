# Integration notes for v18.2

Add to canonical package:

```text
sources/source-quality.json
sources/source-independence.json
sources/source-laundering.json
claims/claim-source-fit.json
claims/claim-evidence-weight.json
reports/citation-quality-index.json
```

Add to final-answer-gate:

```json
{
  "source_quality_gate": {
    "status": "pass|fail",
    "required_artifacts": [
      "sources/source-quality.json",
      "claims/claim-source-fit.json",
      "claims/claim-evidence-weight.json"
    ],
    "validators": [
      "validate_source_quality_schema.py",
      "validate_claim_verdict_requires_weight.py",
      "validate_source_laundering.py",
      "validate_propaganda_mode_separates_truth_from_narrative.py"
    ]
  }
}
```

Renderer must show:

```text
citation id
origin_type
rank_class E0-E5
role/scope label
limitations
```
