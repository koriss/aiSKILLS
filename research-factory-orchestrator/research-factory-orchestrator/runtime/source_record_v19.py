"""Shared v19 source-record normalization for relay bridge and full-research drivers.

Keeps ``sources.json`` aligned with ``schemas/core/sources.schema.json``:
strip unknown keys, map legacy relay enums, fill resolvable locators.
"""
from __future__ import annotations

from typing import Any

# Keys allowed on each source record under ``schemas/core/sources.schema.json``.
SOURCE_SCHEMA_KEYS: frozenset[str] = frozenset(
    {
        "source_id",
        "title",
        "canonical_origin_id",
        "url",
        "document_path",
        "archival_locator",
        "publisher",
        "accessed_at",
        "source_role",
        "access_level",
        "interest_alignment",
        "verification_mode",
        "independence",
        "authority_scope",
        "corroboration_type",
        "citation_eligible",
        "content_snippet",
    }
)


def normalize_source_record_v19(s: dict[str, Any], idx: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Strip non-schema fields into diagnostics; map legacy bridge / driver enums."""
    row_in = dict(s) if isinstance(s, dict) else {}
    diag: dict[str, Any] = {"source_idx": idx}
    snippet_raw = row_in.pop("content_snippet", None)
    if snippet_raw is not None:
        slen = len(str(snippet_raw))
        if slen:
            diag["content_snippet_len"] = slen
    ferr = row_in.pop("content_fetch_error", None)
    if ferr:
        diag["content_fetch_error"] = str(ferr)[:200]
    stripped: list[str] = []
    row: dict[str, Any] = {}
    for k, v in row_in.items():
        if k in SOURCE_SCHEMA_KEYS:
            row[k] = v
        else:
            stripped.append(str(k))
    if stripped:
        diag["stripped_unknown_keys"] = stripped
    if row.get("source_role") == "background":
        row["source_role"] = "unknown"
        diag["mapped_source_role"] = "background→unknown"
    if row.get("source_role") == "authoritative":
        row["source_role"] = "peer_reviewed"
        diag["mapped_source_role"] = "authoritative→peer_reviewed"
    if row.get("interest_alignment") == "neutral":
        row["interest_alignment"] = "unknown"
        diag["mapped_interest_alignment"] = "neutral→unknown"
    ct = row.get("corroboration_type")
    if ct in {"authoritative", "corroborated"}:
        row["corroboration_type"] = "independent"
        diag["mapped_corroboration_type"] = f"{ct}→independent"
    elif ct is not None and ct not in {"independent", "circular", "unknown"}:
        row["corroboration_type"] = "unknown"
        diag["mapped_corroboration_type_fallback"] = str(ct)
    sid_now = str(row.get("source_id") or "").strip() or f"SRC-RELAY-{idx + 1:03d}"
    row["source_id"] = sid_now
    diag["source_id"] = sid_now
    co = str(row.get("canonical_origin_id") or "").strip()
    url = str(row.get("url") or "").strip()
    if not co and url:
        co = url
    if not co:
        co = sid_now
    row["canonical_origin_id"] = co
    title = str(row.get("title") or "").strip() or co[:200]
    row["title"] = title[:200]
    if row.get("citation_eligible") and not (
        row.get("url") or row.get("document_path") or row.get("archival_locator")
    ):
        first = co.split()[0] if co else ""
        if first.startswith("http"):
            row["url"] = first[:2048]
    row.setdefault("access_level", "primary_access")
    row.setdefault("verification_mode", "testimony")
    row.setdefault("independence", "medium")
    row.setdefault("citation_eligible", True)
    row.setdefault("corroboration_type", "unknown")
    row.setdefault("source_role", "unknown")
    row.setdefault("interest_alignment", "unknown")
    if snippet_raw is not None and str(snippet_raw).strip():
        cap = 12000
        t = str(snippet_raw)
        if len(t) > cap:
            t = t[:cap]
            diag["content_snippet_truncated"] = True
        row["content_snippet"] = t
    return row, diag
