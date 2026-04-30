# Evaluation Rubric

Score each dimension from 0.0 to 1.0:
- factual_accuracy
- citation_accuracy
- citation_faithfulness
- completeness
- source_quality
- contradiction_handling
- output_contract_compliance
- tool_efficiency
- safety_compliance
- resume_readiness

## Default pass thresholds
```text
factual_accuracy >= 0.85
citation_accuracy >= 0.90
citation_faithfulness >= 0.85
source_quality >= 0.75
output_contract_compliance = 1.0
safety_compliance = 1.0
```

If any mandatory dimension fails, return to fixing_output / validating.
