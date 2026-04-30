# Embedded Propaganda / IO KB Audit

Generated: 2026-04-27T23:57:25Z

## Key counts

- IO methods: 505
- Propaganda methods v2: 262
- Canonical methods after normalization: 767
- Sources: 2087
- Relations: 4049
- Relation integrity issues: 4049
- Exact crosswalk matches between IO methods and propaganda methods: 389

## Warnings

- Exact title overlaps exist between io-kb methods and PROPAGANDA_METHODS_v2; method-crosswalk is required.
- Some PROPAGANDA_METHODS_v2 records lack definition/mechanism/context/counter; lower match confidence for sparse records.
- Some relations reference IDs absent from loaded primary sets; relation integrity flags are preserved.
- Some source records have missing URLs; they cannot be used as clickable citation sources without enrichment.
- Some source URLs are duplicated; source-origin dedup should collapse duplicate origins.
- KB is analytic reference for classification, not direct evidence about a target entity.
- Do not generate operational influence instructions from method records; use only for detection/classification/counter-analysis.

## Recommendations

- Create canonical IDs across all KB sources.
- Keep raw records, but add normalized canonical-methods, canonical-sources, canonical-relations.
- Add crosswalk from PROPAGANDA_METHODS_v2 method_id to IO_Mxxx when titles/aliases overlap.
- Add field quality_score per method based on definition/mechanism/counter/source_refs presence.
- Treat DTIC/document records as discovery metadata unless full text is available and cited.
- Generate io-method-index.json for safe lexical matching.
- Add kb_match records with safe_use=analytic_classification_only.
- Never allow KB method records to support target facts directly.

Full JSON audit: `kb-audit-report.json`.
