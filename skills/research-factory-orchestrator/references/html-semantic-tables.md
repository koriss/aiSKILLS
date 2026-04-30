
# HTML Semantic Tables

Full HTML report must contain semantic tables, not just narrative sections.

Required columns:

Claims table:
- claim_id;
- claim_text;
- taxonomy;
- verification_status;
- confidence;
- source_ids;
- citation_anchor.

Citation table:
- claim_id;
- source_id;
- anchor;
- supports;
- citation_faithfulness.

Source table:
- source_id;
- title;
- source_type;
- publisher;
- full_url;
- accessed_at;
- supports_claim_ids.

Validation proof table:
- stage;
- artifact;
- validator;
- status;
- sha256.

For person research, identity table:
- profile_id;
- platform;
- url;
- identity_status;
- hard_signals;
- negative_signals;
- used_in_report.



Inline citation table required columns:
- claim_id;
- inline_markers;
- source_ids;
- ref_ids;
- full_urls.
