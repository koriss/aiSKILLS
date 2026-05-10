"""User-facing Markdown deliverables: analysis (with IO) and facts with URLs."""
from __future__ import annotations

import json
import re
from pathlib import Path

from runtime.report_html import build_source_index, load_io_layer_files
from runtime.util import jr


# Characters used in monospace / Unicode tree “tables” — strip for chat payloads.
_BOX_DRAWING = frozenset("│├└┘┌┐┬┴┼─━║═╔╗╚╝╠╣╦╩╬")
def sanitize_chat_body_for_plain_channels(body: str) -> str:
    """Remove ASCII/Unicode pipe tables and box-drawing tree lines.

    Intended for Telegram and other chats where monospace tables mangled readability.
    Fenced ``` blocks are preserved verbatim.
    Markdown pipe-table blocks convert to hyphen bullets (cells joined by em dash).

    References: ``references/plain-text-user-visible-policy.md``, ADR-017 chat roles.
    """
    if not body or not body.strip():
        return body
    lines = body.split("\n")
    out: list[str] = []
    in_fence = False
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(raw)
            i += 1
            continue
        if in_fence:
            out.append(raw)
            i += 1
            continue

        if stripped and _looks_like_md_table_run(lines, i):
            block: list[str] = []
            j = i
            while j < n and lines[j].strip() and _is_md_pipe_table_line(lines[j].strip()):
                block.append(lines[j].strip())
                j += 1
            converted = _md_pipe_table_block_to_bullets(block)
            out.extend(converted if converted else ["- _(tabular block converted to bullets — full detail in HTML report)_"])
            i = j
            continue

        if stripped and _is_box_tree_or_table_line(raw):
            rest = _flatten_tree_line(raw.rstrip("\n")).strip()
            if rest:
                out.append("- " + rest if not rest.startswith(("- ", "• ", "* ")) else rest)
            i += 1
            continue

        out.append(raw)
        i += 1

    return "\n".join(out)


def _compact_for_sep_match(s: str) -> str:
    return s.replace(" ", "").replace("\t", "")


def _is_md_sep_row(s: str) -> bool:
    """GFM separator row: | :--- | :---: | ---: |."""
    compact = _compact_for_sep_match(s)
    if "|" not in compact or "-" not in compact:
        return False
    for part in compact.strip("|").split("|"):
        if not part:
            continue
        if set(part) - set("-:"):
            return False
        if "-" not in part:
            return False
    return True


def _is_md_pipe_table_line(s: str) -> bool:
    st = (s or "").strip()
    if not st:
        return False
    if st.startswith("<"):
        return False
    if _is_md_sep_row(st):
        return True
    return "|" in st and st.count("|") >= 2


def _looks_like_md_table_run(lines: list[str], idx: int) -> bool:
    """Treat as table when separator follows header, or two consecutive dense pipe-rows."""
    if idx >= len(lines):
        return False
    ws = lines[idx].strip()
    if not ws or ws.startswith("```"):
        return False
    if not _is_md_pipe_table_line(ws) or _is_md_sep_row(ws):
        return False
    if idx + 1 >= len(lines):
        return ws.strip().startswith("|") and ws.count("|") >= 2
    nxt = lines[idx + 1].strip()
    if _is_md_sep_row(nxt):
        return True
    if _is_md_pipe_table_line(nxt) and not _is_md_sep_row(nxt):
        return True
    return False


def _md_pipe_row_cells(s: str) -> list[str]:
    chunk = s.strip()
    if chunk.startswith("|"):
        chunk = chunk[1:]
    if chunk.endswith("|"):
        chunk = chunk[:-1]
    cells = [c.strip() for c in chunk.split("|")]
    while cells and cells[-1] == "":
        cells.pop()
    while cells and cells[0] == "":
        cells.pop(0)
    return cells


def _md_pipe_table_block_to_bullets(block: list[str]) -> list[str]:
    bullets: list[str] = []
    sep_idx = next((k for k, ln in enumerate(block) if _is_md_sep_row(ln)), None)
    hdr: list[str] | None = None
    if sep_idx is not None and sep_idx > 0:
        hdr = _md_pipe_row_cells(block[sep_idx - 1])
        body_rows = block[sep_idx + 1 :]
    else:
        body_rows = list(block)

    for row_line in body_rows:
        if _is_md_sep_row(row_line):
            continue
        cells = _md_pipe_row_cells(row_line)
        if not cells:
            continue
        if hdr and len(hdr) == len(cells):
            chunks: list[str] = []
            for h, v in zip(hdr, cells):
                if h and v:
                    chunks.append(f"{h}: {v}")
                elif v:
                    chunks.append(v)
                elif h:
                    chunks.append(str(h))
            bullets.append("- " + " — ".join(chunks))
        else:
            bullets.append("- " + " — ".join(cells))
    return bullets


def _is_box_tree_or_table_line(raw: str) -> bool:
    s = raw.strip()
    if not s:
        return False
    if "├──" in raw or "└──" in raw or "├─" in raw or "└─" in raw:
        return True
    if raw.lstrip().startswith("│"):
        ratio = sum(1 for ch in raw if ch in _BOX_DRAWING or ch == "-") / max(len(raw), 1)
        if ratio > 0.2 and raw.count("|") == 0:
            return True
    if "|" not in raw and "-" * 18 in raw and len(raw.strip()) <= 160:
        if set(raw.strip()) <= set("- ─=\t│"):
            return True
    return False


def _flatten_tree_line(raw: str) -> str:
    s = raw.lstrip("\t ")
    prev = None
    while s != prev:
        prev = s
        s = re.sub(r"^[├└│┘┐┌┬┴┼─\-\+╠═║╚╔╗╝╣╩╦]+[\s│]*", "", s)
    return s.strip()


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

    ft_caps = ""
    ftm = jr(rd / "feature-truth-matrix.json", {})
    ffeats = ftm.get("features") if isinstance(ftm.get("features"), dict) else {}
    if ffeats:
        lines = []
        for k in list(ffeats.keys())[:10]:
            lines.append(f"- `{k}` → `{json.dumps(ffeats[k], ensure_ascii=False)}`")
        ft_caps = (
            "## Capability truth snapshot\n\n"
            "_From `feature-truth-matrix.json` (validator-facing scaffolds, not channel delivery proof)._\n\n"
            + "\n".join(lines)
            + "\n\n"
        )

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
    if ft_caps:
        parts.extend([ft_caps])
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
    return sanitize_chat_body_for_plain_channels("\n".join(parts).strip() + "\n")


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
    return sanitize_chat_body_for_plain_channels("\n".join(lines))


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
