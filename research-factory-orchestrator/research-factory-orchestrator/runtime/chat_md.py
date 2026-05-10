"""User-facing Markdown deliverables: analysis (with IO) and facts with URLs."""
from __future__ import annotations

import json
from pathlib import Path

from runtime.report_html import build_source_index, load_io_layer_files
from runtime.util import jr


def _source_url(s: dict) -> str:
    return str(s.get("full_url") or s.get("url") or "").strip()


def _claim_support_source_ids(claim: dict) -> list[str]:
    out: list[str] = []
    ss = claim.get("support_set")
    if isinstance(ss, list):
        for row in ss:
            if isinstance(row, dict) and row.get("source_id"):
                sid = str(row["source_id"])
                if sid not in out:
                    out.append(sid)
    return out


def apply_facts_gate(claims: list[dict], sources: list[dict]) -> tuple[list[dict], dict]:
    """Downgrade ``confirmed`` / ``probable`` claims that lack URL-backed sources in ``support_set``."""
    lookup = {str(s.get("source_id")): s for s in sources if isinstance(s, dict) and s.get("source_id")}
    out: list[dict] = []
    downgraded: list[str] = []
    for c in claims:
        if not isinstance(c, dict):
            continue
        c2 = dict(c)
        st = str(c2.get("status") or "").lower()
        if st not in ("confirmed", "probable"):
            out.append(c2)
            continue
        has_url = False
        for sid in _claim_support_source_ids(c2):
            src = lookup.get(sid)
            if src and _source_url(src):
                has_url = True
                break
        if not has_url:
            c2["status"] = "unsupported"
            note = c2.get("notes") if isinstance(c2.get("notes"), list) else []
            if not isinstance(note, list):
                note = []
            note.append("facts_gate: downgraded from %s — no URL in support_set sources" % st)
            c2["notes"] = note
            cid = c2.get("claim_id")
            if cid:
                downgraded.append(str(cid))
        out.append(c2)
    meta = {
        "facts_gate_applied": True,
        "downgraded_claim_ids": downgraded,
        "confirmed_without_source_allowed": False,
    }
    return out, meta


def build_analysis_markdown(
    memo: dict,
    io: dict,
    disclaimer: str,
    user_visible_research: bool,
    rd: Path,
) -> str:
    title = str(memo.get("title") or "Analysis")
    summary = str(memo.get("executive_summary") or "").strip()
    conf = str(memo.get("confidence") or "")
    gaps = memo.get("data_gaps")
    gap_lines = ""
    if isinstance(gaps, list) and gaps:
        gap_lines = "\n".join(f"- {g}" for g in gaps if g)

    io_layer = load_io_layer_files(rd)
    mm = io.get("method_matches") if isinstance(io, dict) else []
    mm_txt = ""
    if isinstance(mm, list) and mm:
        mm_txt = "\n".join(json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x) for x in mm[:40])
    else:
        mm_txt = "_(none)_"

    nm = io.get("narrative_map") if isinstance(io, dict) else []
    nm_txt = ""
    if isinstance(nm, list) and nm:
        nm_txt = "\n".join(json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x) for x in nm[:40])
    else:
        nm_txt = "_(none)_"

    extra_io = ""
    if io_layer:
        extra_io = "\n### Raw IO layer files\n\n"
        for key in sorted(io_layer.keys()):
            blob = io_layer[key]
            extra_io += f"#### `{key}`\n\n```json\n{json.dumps(blob, ensure_ascii=False, indent=2)[:12000]}\n```\n\n"

    verdict = str((io or {}).get("verdict") or "n/a")

    parts = [
        f"# {title}",
        "",
        "## Executive summary",
        "",
        summary or "_(empty)_",
        "",
        "## Confidence",
        "",
        f"- Memo confidence: **{conf}**",
        f"- External evidence collected: **{'yes' if user_visible_research else 'no'}**",
        "",
        "## Research disclaimer",
        "",
        disclaimer,
        "",
    ]
    if gap_lines:
        parts.extend(["## Data gaps", "", gap_lines, ""])

    parts.extend(
        [
            "## IO / propaganda check",
            "",
            f"- **Verdict:** `{verdict}`",
            "",
            "### Method matches (summary)",
            "",
            mm_txt,
            "",
            "### Narrative map (summary)",
            "",
            nm_txt,
            "",
        ]
    )
    parts.append(extra_io.rstrip())
    return "\n".join(parts).strip() + "\n"


def build_facts_markdown(claims: list[dict], sources: list[dict]) -> str:
    idx = build_source_index(sources)
    by_id = {str(s.get("source_id")): s for s in sources if isinstance(s, dict) and s.get("source_id")}
    lines: list[str] = [
        "# Facts and linked sources",
        "",
        "Each claim lists wiki-style source indices [[n]] matching `report/full-report.html` references.",
        "",
    ]
    for i, c in enumerate(claims, start=1):
        if not isinstance(c, dict):
            continue
        cid = str(c.get("claim_id") or "")
        text = str(c.get("claim_text") or c.get("text") or "").strip()
        st = str(c.get("status") or "")
        conf = str(c.get("confidence") or "")
        sids = _claim_support_source_ids(c)
        ref_nums = []
        url_lines = []
        for sid in sids:
            n = idx.get(sid)
            if n is not None:
                ref_nums.append(f"[{n}]")
            src = by_id.get(sid)
            if src:
                url = _source_url(src)
                t = str(src.get("title") or "")[:120]
                if url:
                    url_lines.append(f"- <{url}> — _{t}_ (`{sid}`)")
                else:
                    url_lines.append(f"- _(no URL)_ — `{sid}`")
            else:
                url_lines.append(f"- _(unknown source)_ `{sid}`")

        lines.append(f"## {i}. `{cid}`")
        lines.append("")
        lines.append(f"- **Status:** `{st}`  ")
        lines.append(f"- **Confidence:** `{conf}`  ")
        if ref_nums:
            lines.append(f"- **Refs:** {' '.join(ref_nums)}")
        lines.append("")
        lines.append(text or "_(no text)_")
        lines.append("")
        lines.append("**Sources:**")
        lines.append("")
        if url_lines:
            lines.extend(url_lines)
        else:
            lines.append("- _(no sources in support_set)_")
        lines.append("")
    if len(lines) <= 5:
        lines.append("_(no claims)_\n")
    return "\n".join(lines)


def compute_quality_metadata(
    rd: Path,
    seed_only: bool,
    facts_gate_meta: dict,
    claims: list[dict],
    sources: list[dict],
) -> dict:
    """Machine-readable quality flags for ``result-manifest.json`` / optional ``result.json``."""
    coll = jr(rd / "collection-result.json", {})
    any_url = bool(any(_source_url(s) for s in sources if isinstance(s, dict)))
    seed_stub = False
    hydrated = False
    for c in claims or []:
        if not isinstance(c, dict):
            continue
        meta = c.get("meta") if isinstance(c.get("meta"), dict) else {}
        if meta.get("origin") == "seed_only_stub":
            seed_stub = True
        if meta.get("origin") == "hydrate_from_sources":
            hydrated = True
    return {
        "seed_only": bool(seed_only),
        "facts_have_links": any_url,
        "io_check_in_analysis": True,
        "confirmed_without_source_allowed": False,
        "facts_gate": facts_gate_meta,
        "collection_seed_only": bool(isinstance(coll, dict) and coll.get("seed_only")),
        "synthetic_claim_markers": {
            "seed_only_stub": seed_stub,
            "hydrated_from_sources": hydrated,
        },
    }
