# BUILD REPORT — IO KB UNIFIED v1.0

**Date:** 2026-04-22  
**Build ID:** io-kb-unified-2026-04-22  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

Built unified knowledge base from all available sources. Total: **8,666 entities** across 8 layers.

---

## LAYER SUMMARY

| Layer | Count | Source Data | KB Size |
|-------|-------|-------------|---------|
| methods | 505 | IO KB (331) + Propaganda KB (174) | 473 KB |
| actors | 26 | IO KB actors | 7.3 KB |
| doctrines | 11 | IO KB doctrines | 3.9 KB |
| sources | 2,087 | Bibliography (1,957) + Non-English (130) | 787 KB |
| documents | 1,946 | DTIC meta records | 1.2 MB |
| relations | 4,049 | Cross-layer links | 561 KB |
| languages | 17 | ISO 639-1 | 1.8 KB |
| regions | 25 | ISO 3166-1 + extended | 2.7 KB |
| **TOTAL** | **8,666** | | **3.0 MB** |

---

## PIPELINE STAGES

| Stage | Status | Notes |
|-------|--------|-------|
| 1. DISCOVERY | ✅ | Found all source files |
| 2. EXTRACTION | ✅ | All layers extracted |
| 3. NORMALIZATION | ✅ | Language codes, country codes unified |
| 4. DEDUP | ✅ | 500 dupes removed from documents |
| 5. STRUCTURING | ✅ | Uniform JSON schema |
| 6. LINKING | ✅ | 4,049 relations built |
| 7. VALIDATION | ✅ | Schema compliance checked |
| 8. OUTPUT | ✅ | All files written |

---

## DATA SOURCES

### IO Knowledge Base
- 331 methods
- 26 actors (IRA, GRU, IRGC, IDF, 650th CFR, etc.)
- 11 doctrines (JP 3-13, NATO AJP-3.10, Chinese Three Warfares, etc.)

### Propaganda Knowledge Base v2
- 174 methods from 21 sources
- CIPSO Detection (57), Кара-Мурза (22), Bernays (9), Linebarger (9), etc.

### Bibliography
- 1,957 entries (EN:932, RU:308, ZH:193, DE:162, HE:104, ES:70, FR:20, AR:6)

### Non-English Sources
- 130 sources (HE:30, FA:22, TR:18, PT:18, HI:16, AR:16, JA:5, KO:5)

### DTIC
- 1,946 documents with metadata
- 1,302 IO-relevant (67%)

---

## RELATION TYPES

| Type | Count |
|------|-------|
| source → language | 2,087 |
| document → method | 1,747 |
| method → source_ref | 174 |
| actor → country | 26 |
| doctrine → language | 15 |

---

## NOTES

- DTIC full-text not indexed (212 MB extracted text)
- Relations are directional (from→to)
- Language codes: ISO 639-1
- Country codes: mixed (some ISO 3166-1, some full names)
- confidence scores: IO=0.85, PROP=0.8, DTIC=0.7, BIB=0.7

---

**END REPORT**