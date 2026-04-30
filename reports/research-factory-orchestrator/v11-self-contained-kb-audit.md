# v11 Self-Contained KB Audit

## Embedded KB

The propaganda / IO archive is embedded under:

```text
skills/research-factory-orchestrator/kb/propaganda-io/
```

No external `/research-kb/...` path is required.

## Normalized records

```json
{
  "canonical_records": 4837,
  "canonical_methods": 767,
  "canonical_sources": 2087,
  "canonical_relations": 4049,
  "method_crosswalk_records": 389,
  "search_index_records": 804
}
```

## Content diagnostics summary

```json
{
  "methods_title_duplicate_groups": 170,
  "propaganda_title_duplicate_groups": 1,
  "cross_exact_title_matches_count": 184,
  "relations_broken_count": 4049,
  "sources_missing_url": 1517,
  "sources_duplicate_url_groups": 43
}
```

## Important warnings

- Exact title overlaps exist between io-kb methods and PROPAGANDA_METHODS_v2; method-crosswalk is required.
- Some PROPAGANDA_METHODS_v2 records lack definition/mechanism/context/counter; lower match confidence for sparse records.
- Some relations reference IDs absent from loaded primary sets; relation integrity flags are preserved.
- Some source records have missing URLs; they cannot be used as clickable citation sources without enrichment.
- Some source URLs are duplicated; source-origin dedup should collapse duplicate origins.
- KB is analytic reference for classification, not direct evidence about a target entity.
- Do not generate operational influence instructions from method records; use only for detection/classification/counter-analysis.

## Refactor performed

- raw archive preserved;
- original KB directories preserved;
- canonical records generated;
- canonical methods generated;
- canonical sources generated;
- canonical relations generated with generated relation IDs;
- exact title/alias crosswalk generated between IO KB methods and propaganda methods;
- compact method/actor/doctrine search index generated;
- query/match scripts added;
- validators added for embedded KB, no external KB dependency, no dangling required artifact links and safe IO output.
