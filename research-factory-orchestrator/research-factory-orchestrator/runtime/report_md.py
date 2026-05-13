"""Canonical Markdown dossier: single human-readable layer before HTML (MD-first)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from runtime.report_inputs import ReportRunInputs
from runtime.util import CLAIM_STATUS_LEGACY_ALIASES, tw

FULL_REPORT_MD_REL = "report/full-report.md"


def _source_index(sources: list[dict]) -> dict[str, int]:
    ids: list[str] = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = s.get("source_id")
        if sid is not None and str(sid) not in ids:
            ids.append(str(sid))
    ids.sort()
    return {sid: i + 1 for i, sid in enumerate(ids)}


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


def _normalize_claim_status_for_bucket(status: object) -> str:
    s = str(status or "").strip().lower()
    if not s:
        return ""
    meta = CLAIM_STATUS_LEGACY_ALIASES.get(s)
    if isinstance(meta, dict):
        use = meta.get("use")
        if isinstance(use, str) and use.strip():
            return use.strip().lower()
    return s


def _claim_bucket(status: object) -> str:
    s = _normalize_claim_status_for_bucket(status)
    if s in ("confirmed", "verified", "established", "confirmed_fact", "established_fact"):
        return "verified"
    if s in ("disputed", "contradicted", "rejected", "false"):
        return "disputed"
    return "uncertain"


def _md_cell(s: str) -> str:
    t = str(s).replace("|", "\\|").replace("\n", " ").strip()
    return t or "—"


def _md_fence(label: str, obj: object) -> str:
    body = json.dumps(obj, ensure_ascii=False, indent=2)
    if len(body) > 12000:
        body = body[:12000] + "\n… (truncated)\n"
    return f"```{label}\n{body}\n```\n"


def build_full_report_md(inp: ReportRunInputs) -> str:
    """Deterministic Markdown from the same JSON inputs as the legacy HTML template path."""
    from runtime.status import VERSION
    from runtime.util import now as util_now

    idx = _source_index(inp.sources)
    lines: list[str] = []
    gen_at = util_now()
    title = f"# RFO full report — {inp.run_id}"
    lines.append(title)
    lines.append("")
    lines.append(f"_Generated (UTC): `{gen_at}` · skill_version `{VERSION}` · mode `{inp.run_meta.get('mode', '')}`_")
    lines.append("")
    lines.append("## Run metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| run_id | `{_md_cell(inp.run_id)}` |")
    lines.append(f"| job_id | `{_md_cell(inp.job_id)}` |")
    lines.append(f"| command_id | `{_md_cell(inp.cmd_id)}` |")
    lines.append(f"| provider | `{_md_cell(inp.provider)}` |")
    lines.append(f"| user_visible_research | `{inp.user_visible_research}` |")
    lines.append(f"| disclaimer | {_md_cell(inp.disclaimer)} |")
    lines.append("")
    lines.append("## Research task")
    lines.append("")
    lines.append(inp.task.strip() or "_(empty task in run.json)_")
    lines.append("")
    lines.append("## Executive summary (analytical memo)")
    lines.append("")
    lines.append(str(inp.memo.get("executive_summary") or "_(no executive_summary)_").strip() or "_(empty)_")
    lines.append("")
    lines.append(f"**Title:** {_md_cell(str(inp.memo.get('title') or ''))}")
    lines.append(f"**Confidence (memo):** `{_md_cell(str(inp.memo.get('confidence') or ''))}`")
    lines.append("")
    gaps = inp.memo.get("data_gaps")
    lines.append("### Data gaps")
    lines.append("")
    if isinstance(gaps, list) and gaps:
        for g in gaps:
            lines.append(f"- {_md_cell(str(g))}")
    else:
        lines.append("_No data_gaps entries._")
    lines.append("")
    lines.append("## Factual dossier (counts)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| claims_total | `{inp.factual.get('claims_total', '')}` |")
    lines.append(f"| sources_total | `{inp.factual.get('sources_total', '')}` |")
    lines.append(f"| evidence_cards_total | `{inp.factual.get('evidence_cards_total', '')}` |")
    lines.append("")
    lines.append("## IO / propaganda check")
    lines.append("")
    lines.append(f"**Verdict:** `{_md_cell(str(inp.io.get('verdict', 'n/a')))}`")
    lines.append("")
    lines.append("## Self-audit (deviations)")
    lines.append("")
    devs = inp.audit.get("deviations") if isinstance(inp.audit, dict) else []
    if isinstance(devs, list) and devs:
        for d in devs:
            lines.append(f"- `{_md_cell(json.dumps(d, ensure_ascii=False))}`")
    else:
        lines.append("_No deviations recorded._")
    lines.append("")
    lines.append("## Graph & waves (summary)")
    lines.append("")
    lines.append(
        f"- Nodes: **{len(inp.nodes)}** · Edges: **{len(inp.edges)}** · Waves: **{len(inp.waves)}** · "
        f"Evidence cards: **{len(inp.evidence)}**"
    )
    lines.append("")
    if inp.waves:
        lines.append(_md_fence("json", inp.waves[:25]))
    lines.append("")
    for bucket, label in (
        ("verified", "Claims — verified"),
        ("nonverified", "Claims — non-verified / uncertain / disputed mix"),
        ("disputed", "Claims — disputed"),
    ):
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| claim_id | status | confidence | text | wiki refs |")
        lines.append("| --- | --- | --- | --- | --- |")
        n = 0
        for c in inp.claims:
            if not isinstance(c, dict):
                continue
            b = _claim_bucket(c.get("status"))
            if bucket == "verified" and b != "verified":
                continue
            if bucket == "nonverified" and b == "verified":
                continue
            if bucket == "disputed" and b != "disputed":
                continue
            sids = _claim_support_source_ids(c)
            refs = ", ".join(f"[{idx.get(s, '?')}]" for s in sids if idx.get(s)) or "—"
            text = str(c.get("claim_text") or c.get("text") or "")
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 240:
                text = text[:240] + "…"
            lines.append(
                f"| `{_md_cell(str(c.get('claim_id') or ''))}` | "
                f"`{_md_cell(str(c.get('status') or ''))}` | "
                f"`{_md_cell(str(c.get('confidence') or ''))}` | "
                f"{_md_cell(text)} | {refs} |"
            )
            n += 1
            if n >= 80:
                break
        if n == 0:
            lines.append("_(none in this bucket)_")
        lines.append("")
    lines.append("## Sources (numbered references)")
    lines.append("")
    lines.append("| n | source_id | title | url | publisher | accessed_at |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    by_n: dict[int, dict] = {}
    for s in inp.sources:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("source_id") or "")
        n = idx.get(sid)
        if n is not None:
            by_n[n] = s
    for n in sorted(by_n.keys()):
        s = by_n[n]
        url = str(s.get("full_url") or s.get("url") or "")
        lines.append(
            f"| {n} | `{_md_cell(str(s.get('source_id') or ''))}` | "
            f"{_md_cell(str(s.get('title') or ''))} | "
            f"`{_md_cell(url)}` | {_md_cell(str(s.get('publisher') or ''))} | "
            f"`{_md_cell(str(s.get('accessed_at') or ''))}` |"
        )
    if not by_n:
        lines.append("| — | — | — | — | — | — |")
    lines.append("")
    lines.append("## Evidence card excerpts")
    lines.append("")
    for e in inp.evidence[:40]:
        if not isinstance(e, dict):
            continue
        eid = str(e.get("evidence_id") or e.get("evidence_card_id") or "")
        ex = e.get("extracted_fact_or_excerpt")
        text = ""
        if isinstance(ex, dict):
            text = str(ex.get("text") or ex.get("kind") or "")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 400:
            text = text[:400] + "…"
        lines.append(f"- **`{eid}`** — {text or '_(no excerpt)_'}")
    if len(inp.evidence) > 40:
        lines.append(f"- _… {len(inp.evidence) - 40} more evidence cards omitted._")
    lines.append("")
    lines.append("## Machine contract")
    lines.append("")
    lines.append(
        "This file is produced **only** from JSON artifacts under the run directory. "
        "HTML at `report/full-report.html` is a **derivative** render of this Markdown (MD-first pipeline)."
    )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_canonical_full_report_md(rd: Path, md_doc: str, *, source: str = "unknown") -> Path:
    _ = source
    p = Path(rd).resolve() / FULL_REPORT_MD_REL
    tw(p, md_doc)
    return p
