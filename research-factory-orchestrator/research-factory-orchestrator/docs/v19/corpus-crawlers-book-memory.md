# Corpus, crawler agents & book memory (design synthesis, v19)

Design-only synthesis for a **traceable research factory**: crawling and memory layers exist to produce and rank **candidate** material for Sources and Evidence cards; they must not bypass [Sacred Path](./sacred-path-contract.md).

## Layering (mental model)

| Layer | Role | Outputs toward RFO |
|-------|------|---------------------|
| **Collection** | Lawful acquisition, robots/sitemap/API-first, politeness | Raw snapshots + fetch logs |
| **Normalization** | Extract text/metadata, OCR/ASR routers, canonical URLs | Normalized documents |
| **Evidence plane** | Provenance stamping, evidence cards, claim assembly | `sources` / `evidence` / `claims` bundles |
| **Memory plane** | Corpus index, editions, vectors (optional), graph (optional) | Retrieval **candidates** + context only |
| **Generation & validation** | Drafting from claims, V1–V6, delivery | Reports + transcripts |

**Book memory** and **corpus index** live primarily in the **memory plane**: versioned reference (definitions, methods, stable legal text, theory) and volatile web/news layers respectively. Neither replaces primary evidence for **current** operational facts without meeting claim-type policy.

## Crawler / agent design principles

- **Prefer** official API, dumps, sitemaps, structured feeds over blind site recursion.
- **Robots.txt** (RFC 9309): coordinate politeness; not authorization. Complement with ToS/licensing review per domain.
- **Conditional requests**: `If-None-Match`, `If-Modified-Since`, honor `304`, `Retry-After`, `429`, `503`.
- **Identity**: meaningful `User-Agent` with contact; do not impersonate browsers to evade policy.
- **Provenance**: final URL, redirect chain, timestamps, content hash, MIME — mandatory linkage into Source records.
- **Archival**: WARC or equivalent for reproducibility where policy allows.

## Book memory

- **Unit**: edition-aware, page- or locator-bound chunks; `citation_ready` only with stable locator.
- **Rule**: a book chunk **alone** does not prove a **post-publication** current event; it may cap or contextualize. Exceptions: stable definitions, law-as-text, historical claims explicitly scoped.
- **Ingestion**: catalog metadata (ISBN, DOI, national library records) before random PDFs from unknown mirrors.

## Corpus index

- Holds **map** of corpus (seeds, duplicate groups, chunk manifest), not a substitute for per-run evidence cards.
- **Dedup**: `canonical_origin_id` for independence counting (see Sacred Path contract).

## Retrieval policy (sketch)

1. Classify `claim_type` and temporal scope.  
2. Current factual / legal → prefer official web + primary documents.  
3. Definitional / methodological → allow book memory **as context**; upgrade to support only per D3 caps.  
4. Narrative / propagation → origin + amplification in web corpus; book memory for terminology only.  
5. Weak retrieval → `insufficient_evidence`, not synthesis from memory alone.

## Legal / ethics (design obligations)

- Data minimization, purpose limitation, retention/redaction; jurisdiction-specific review for scraping, TDM, PII.  
- Copyright: store **license-allowed** full text or minimal excerpt + metadata + rights registry; takedown path.  
- Disinformation work: avoid building an automated “truth verdict” machine; use neutral patterns + HITL for high-stakes topics.

## Relation to implementation

This document does **not** mandate a tech stack (Scrapy, Playwright, Qdrant, etc.). Phase 1 implementation remains **contracts + validators + fixtures** per [IMPLEMENTATION-PHASE-1-HANDOFF](./IMPLEMENTATION-PHASE-1-HANDOFF.md); crawler/memory services are a **later** track once Sacred Path and six validators are green.

## References (external standards & practices)

Standards worth citing in runbooks: RFC 9309 (robots), RFC 9110 / 6585 (HTTP semantics, 429), WARC (ISO 28500 family), PROV, Web Annotation, IIIF where audiovisual artifacts apply, Schema.org / Dublin Core for metadata hooks. Product docs (sitemaps, Crossref, publisher APIs) should be listed in an operational `sources-seed-list` when implementation starts — not duplicated here as URL laundry.
