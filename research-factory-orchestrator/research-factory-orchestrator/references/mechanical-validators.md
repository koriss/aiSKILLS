
# Mechanical Validators

The skill must not rely only on prose rules.

Before final delivery, run validators when file execution is available:

- `validate_html_report.py`
- `validate_final_answer_gate.py`
- `validate_summary_no_new_claims.py`
- `validate_item.py`
- `validate_all_items.py`
- `validate_artifact_manifest.py`
- `validate_package.py`
- `security_scan_skill.py`

If validators cannot run, perform equivalent manual checks and record that limitation in `final-answer-gate.json`.

No validator pass = no final delivery.


Additional v7 validators:

- `validate_completion_proof.py`
- `validate_search_ledger.py`
- `validate_evidence_debt.py`
- `validate_research_package.py`
- `validate_stage_records.py`
- `validate_claim_citation_links.py`
- `validate_validation_transcript.py`
- `validate_no_pipeline_claims_without_artifacts.py`

Final delivery requires completion proof and validation transcript.



Additional v8 validators:
- `validate_research_package_zip.py`
- `validate_identity_resolution.py`
- `validate_social_profile_linkage.py`
- `validate_no_name_only_matches.py`
- `validate_identity_conflicts.py`
- `validate_person_profile_claims.py`
- `validate_person_data_classification.py`
- `validate_no_global_overclaiming.py`
- `validate_html_semantic_tables.py`
- `validate_html_source_links.py`



Additional v9 validators:
- `validate_wiki_inline_citations.py`
- `validate_coverage_matrix.py`
- `validate_no_premature_stopping.py`
- `validate_unsearched_categories.py`
- `validate_claim_citation_map.py`
- `validate_person_data_classification.py`


Additional v10 validators:

- `validate_workplan.py`
- `validate_shard_contracts.py`
- `validate_shard_outputs.py`
- `validate_shard_ledger.py`
- `validate_retry_ledger.py`
- `validate_resume_plan.py`
- `validate_watchdog_state.py`
- `validate_global_merge.py`
- `validate_no_unmerged_shards.py`
- `validate_no_shard_scope_reduction.py`
- `validate_int_coverage_matrix.py`
- `validate_no_single_int_lockin.py`
- `validate_collection_feasibility.py`
- `validate_no_fake_int_claims.py`
- `validate_source_provenance.py`
- `validate_all_source_fusion.py`
- `validate_source_family_confidence.py`
- `validate_no_all_int_overclaiming.py`
