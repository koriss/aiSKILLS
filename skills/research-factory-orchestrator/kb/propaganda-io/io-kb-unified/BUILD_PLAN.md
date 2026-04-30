# IO KB UNIFIED BUILD PLAN
**Date:** 2026-04-22  
**Status:** IN PROGRESS

---

## ARCHITECTURE

```
io-kb-unified/
├── methods.jsonl      ← IO methods (331) + Propaganda methods (174)
├── actors.jsonl       ← Countries, orgs, structures
├── doctrines.jsonl    ← Military doctrines, concepts, strategies
├── sources.jsonl      ← Books, documents, articles, PDFs
├── documents.jsonl   ← Concrete texts, extracted data
├── relations.jsonl    ← All cross-entity links
├── languages.jsonl    ← Language registry
├── regions.jsonl      ← Country/region registry
├── reports/
│   ├── BUILD_REPORT.md
│   ├── DATA_QUALITY.md
│   ├── COVERAGE.md
└── state/
    ├── BUILD_STATE.json
    └── RUN_LOG.md
```

---

## PIPELINE STAGES

### Stage 1: DISCOVERY ✅
- Find all relevant files
- Inventory by type/count/size
- Understand data structures

### Stage 2: EXTRACTION
- Extract methods from IO KB (331) + Propaganda KB (174)
- Extract actors from IO KB (26)
- Extract doctrines from IO KB (11)
- Extract bibliography entries
- Extract non-English sources (130 from SOURCES_ACCEPTED)
- Extract DTIC metadata (6107 files, 1946 with meta.json)

### Stage 3: NORMALIZATION
- Unify language codes (ISO 639-1)
- Unify country codes (ISO 3166-1 alpha-2)
- Normalize method categories
- Normalize actor types
- Unify source types

### Stage 4: DEDUP
- Exact dedup by ID
- Exact dedup by URL
- Semantic dedup by title (normalized)

### Stage 5: STRUCTURING
- Convert all to uniform JSON schema
- Each entity: id, name, aliases, description, metadata, source_ids, confidence

### Stage 6: LINKING
- method → method (hierarchical, sequential, contrasting)
- method → actor (who uses it)
- method → doctrine (where documented)
- method → source (where found)
- actor → doctrine (who authored/adopted)
- source → language
- source → region

### Stage 7: VALIDATION
- Check all required fields
- Check referential integrity
- Check for orphaned relations

### Stage 8: OUTPUT
- Write all .jsonl files
- Write reports

---

## OUTPUT SCHEMAS

### methods.jsonl
```json
{"id":"...","kb_source":"io|propaganda","name":{},"aliases":[],"category":"...","subcategory":"...","description":{},"mechanism":"...","source_ids":[],"language":"...","confidence":0.9,"related_methods":[],"used_by_actors":[],"doctrina_ids":[]}
```

### actors.jsonl
```json
{"id":"...","type":"state|org|structure","name":{},"country":"...","description":{},"io_methods":[],"doctrines":[],"sources":[],"confidence":0.9}
```

### doctrines.jsonl
```json
{"id":"...","name":{},"country":"...","year":2020,"type":"military|concept|strategy","description":{},"methods":[],"actors":[],"sources":[],"confidence":0.9}
```

### sources.jsonl
```json
{"id":"...","type":"book|article|pdf|doctrine|report|paper","title":{},"author":"...","year":2020,"language":"...","country":"...","url":"...","format":"pdf|html|text","topic_tags":[],"relevance_score":8,"why_relevant":"...","confidence":0.9}
```

### documents.jsonl
```json
{"id":"...","type":"dtic|web|extracted","source_id":"...","title":"...","language":"...","country":"...","content_hash":"...","file_path":"...","methods_found":[],"actors_found":[],"confidence":0.9}
```

### relations.jsonl
```json
{"from_id":"...","from_type":"method|actor|doctrine|source","relation":"uses|documents|belongs_to|related_to|cites","to_id":"...","to_type":"...","metadata":{}}
```

---

## PROGRESS TRACKING

| Stage | Status | Methods | Actors | Doctrines | Sources | Documents | Relations |
|-------|--------|---------|--------|-----------|---------|-----------|-----------|
| 1 DISCOVERY | ✅ | - | - | - | - | - | - |
| 2 EXTRACTION | 🔄 | - | - | - | - | - | - |
| 3 NORMALIZE | ⬜ | - | - | - | - | - | - |
| 4 DEDUP | ⬜ | - | - | - | - | - | - |
| 5 STRUCTURE | ⬜ | - | - | - | - | - | - |
| 6 LINKING | ⬜ | - | - | - | - | - | - |
| 7 VALIDATE | ⬜ | - | - | - | - | - | - |
| 8 OUTPUT | ⬜ | - | - | - | - | - | - |