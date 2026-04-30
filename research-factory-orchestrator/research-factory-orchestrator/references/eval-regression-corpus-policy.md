
# Eval Regression Corpus Policy

Each real failure becomes an eval case.

Required fields:
- case_id
- failure_type
- bad_output_pattern
- expected_guard
- validator
- eval_assertion

A new version is not ready if it fails known regression cases.
