
# v7 Proof Audit

## Problem

v4 showed that a model can claim the strict pipeline was executed without producing proof artifacts.

## v7 Fix

v7 adds proof-of-work artifacts:

- `completion-proof.json`
- `research-package.json`
- `search-ledger.json`
- `evidence-debt.json`
- `validation-transcript.json`
- `stage-records/`

And validators:

- `validate_completion_proof.py`
- `validate_search_ledger.py`
- `validate_evidence_debt.py`
- `validate_research_package.py`
- `validate_stage_records.py`
- `validate_claim_citation_links.py`
- `validate_validation_transcript.py`
- `validate_no_pipeline_claims_without_artifacts.py`

## New Rule

No artifact proof = no pipeline claim.

No completion-proof = no final delivery.
