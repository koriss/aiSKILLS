"""Standalone HTML report assembly: wiki-style citations, template fill, IO/propaganda blocks."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from runtime.report_inputs import ReportRunInputs, minimal_report_sources_ready
from runtime.report_md import (
    FULL_REPORT_MD_REL,
    build_full_report_md,
    write_canonical_full_report_md,
)
from runtime.util import CLAIM_STATUS_LEGACY_ALIASES, jr, tw

# Canonical relative path inside a run-dir (single writer API — use write_canonical_full_report_html).
FULL_REPORT_REL = "report/full-report.html"

# Standard JSON proof block ids expected by ``scripts/validate_html_proof_matches_runtime_artifacts.py``.
_RFO_BLOCK_TO_FILE: tuple[tuple[str, str], ...] = (
    ("runtime-status-json", "runtime-status.json"),
    ("entrypoint-proof-json", "entrypoint-proof.json"),
    ("delivery-manifest-json", "delivery-manifest.json"),
    ("final-answer-gate-json", "final-answer-gate.json"),
    ("validation-transcript-json", "validation-transcript.json"),
    ("artifact-manifest-json", "artifact-manifest.json"),
    ("provenance-manifest-json", "provenance-manifest.json"),
    ("semantic-report-json", "report/semantic-report.json"),
)

_PKG_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = _PKG_ROOT / "templates" / "full-report-template.html"

_IO_LAYER_FILES = (
    "narrative-map.json",
    "io-method-matches.json",
    "source-laundering-map.json",
    "amplification-chain.json",
)


def fill_template(template: str, mapping: dict[str, str]) -> str:
    """Replace {{KEY}} placeholders; unknown keys become explicit gap notice."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in mapping:
            return mapping[key]
        return '<p><em>Данные отсутствуют в артефактах (' + html.escape(key) + ").</em></p>"

    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", repl, template)


def build_source_index(sources: list[dict]) -> dict[str, int]:
    """Stable source_id → 1-based index for wiki refs."""
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


def render_ref_markers(source_ids: list[str], idx: dict[str, int]) -> str:
    parts: list[str] = []
    for sid in source_ids:
        n = idx.get(sid)
        if n is None:
            continue
        parts.append(
            f'<sup class="ref-marker"><a href="#ref-{n}">[{n}]</a></sup>'
        )
    return "".join(parts)


def render_wiki_references(sources: list[dict], idx: dict[str, int]) -> str:
    """Ordered list items id=ref-n compatible with sample-full-report."""
    by_n: dict[int, dict] = {}
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("source_id") or "")
        n = idx.get(sid)
        if n is not None:
            by_n[n] = s
    parts: list[str] = []
    for n in sorted(by_n.keys()):
        s = by_n[n]
        url = html.escape(str(s.get("full_url") or s.get("url") or ""))
        title = html.escape(str(s.get("title") or ""))
        sid = html.escape(str(s.get("source_id") or ""))
        pub = html.escape(str(s.get("publisher") or ""))
        acc = html.escape(str(s.get("accessed_at") or ""))
        line = f'<li id="ref-{n}">'
        if url:
            line += f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a><br>'
        line += f"<small>{sid}"
        if title:
            line += f" — {title}"
        if pub:
            line += f" · {pub}"
        if acc:
            line += f" · accessed {acc}"
        line += "</small></li>"
        parts.append(line)
    if not parts:
        return "<li><em>Нет источников для нумерованных ссылок.</em></li>"
    return "".join(parts)


def render_source_table_rows(sources: list[dict]) -> str:
    rows: list[str] = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        cids = s.get("supports_claim_ids")
        if isinstance(cids, list):
            cids_s = html.escape(", ".join(str(x) for x in cids))
        else:
            cids_s = ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(s.get('source_id') or ''))}</td>"
            f"<td>{html.escape(str(s.get('title') or ''))}</td>"
            f"<td>{html.escape(str(s.get('source_type') or ''))}</td>"
            f"<td>{html.escape(str(s.get('publisher') or ''))}</td>"
            f"<td>{html.escape(str(s.get('full_url') or s.get('url') or ''))}</td>"
            f"<td>{html.escape(str(s.get('accessed_at') or ''))}</td>"
            f"<td>{cids_s}</td>"
            "</tr>"
        )
    return "".join(rows) or "<tr><td colspan='7'><em>Нет источников.</em></td></tr>"


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


def render_claim_cards_html(claims: list[dict], idx: dict[str, int], bucket: str | None) -> str:
    """bucket: verified | uncertain | disputed | nonverified (not verified) | None (all)."""
    cards: list[str] = []
    for c in claims:
        if not isinstance(c, dict):
            continue
        b = _claim_bucket(c.get("status"))
        if bucket == "verified" and b != "verified":
            continue
        if bucket == "uncertain" and b != "uncertain":
            continue
        if bucket == "disputed" and b != "disputed":
            continue
        if bucket == "nonverified" and b == "verified":
            continue
        cid = html.escape(str(c.get("claim_id") or "n/a"))
        text = str(c.get("claim_text") or c.get("text") or "")
        conf = html.escape(str(c.get("confidence") or ""))
        st = html.escape(str(c.get("status") or ""))
        css = "verified" if b == "verified" else ("danger" if b == "disputed" else "warning")
        sids = _claim_support_source_ids(c)
        markers = render_ref_markers(sids, idx)
        no_anchor = ""
        if not sids and text:
            no_anchor = ' <span class="chip">no source anchor</span>'
        cards.append(
            f'<article class="card claim-card {css}"><h3>{cid}</h3>'
            f"<p>{html.escape(text)}{markers}{no_anchor}</p>"
            f'<div class="claim-meta"><span class="chip {css}">{st}</span>'
            f'<span class="chip">Confidence: {conf}</span></div></article>'
        )
    if not cards:
        return "<p><em>Нет утверждений в этой категории.</em></p>"
    return f'<div class="grid">{"".join(cards)}</div>'


def load_io_layer_files(rd: Path) -> dict[str, object]:
    out: dict[str, object] = {}
    io_dir = rd / "io"
    if not io_dir.is_dir():
        return out
    for fname in _IO_LAYER_FILES:
        p = io_dir / fname
        if not p.is_file():
            continue
        key = fname.replace(".json", "").replace("-", "_")
        data = jr(p, None)
        if data is not None:
            out[key] = data
    return out


def build_io_propaganda_html(io: dict[str, object], io_layer: dict[str, object]) -> str:
    parts: list[str] = []
    verdict = io.get("verdict", "n/a")
    parts.append(f"<p><strong>Вердикт IO:</strong> <code>{html.escape(str(verdict))}</code></p>")

    mm = io.get("method_matches")
    if isinstance(mm, list) and mm:
        parts.append("<h3>Совпадения с методами IO</h3><ul>")
        for item in mm:
            if isinstance(item, dict):
                parts.append(f"<li>{html.escape(json.dumps(item, ensure_ascii=False))}</li>")
            else:
                parts.append(f"<li>{html.escape(str(item))}</li>")
        parts.append("</ul>")
    else:
        parts.append("<p><em>В сводке method_matches нет записей.</em></p>")

    nm = io.get("narrative_map")
    if isinstance(nm, list) and nm:
        parts.append("<h3>Narrative map (сводка)</h3><ul>")
        for item in nm:
            if isinstance(item, dict):
                parts.append(f"<li>{html.escape(json.dumps(item, ensure_ascii=False))}</li>")
            else:
                parts.append(f"<li>{html.escape(str(item))}</li>")
        parts.append("</ul>")

    nm_file = io_layer.get("narrative_map")
    if isinstance(nm_file, dict) and isinstance(nm_file.get("narratives"), list):
        rows = nm_file["narratives"]
        if rows:
            parts.append("<h3>Narrative lines (io/narrative-map.json)</h3>")
            parts.append(
                "<table><thead><tr><th>ID</th><th>Claim</th><th>Confidence</th></tr></thead><tbody>"
            )
            for row in rows:
                if not isinstance(row, dict):
                    continue
                parts.append(
                    "<tr>"
                    f"<td>{html.escape(str(row.get('narrative_id', '')))}</td>"
                    f"<td>{html.escape(str(row.get('claim', '')))}</td>"
                    f"<td>{html.escape(str(row.get('confidence', '')))}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table>")

    if io_layer:
        parts.append("<h3>Прочие артефакты каталога io/</h3>")
        for key in sorted(io_layer.keys()):
            if key == "narrative_map":
                continue
            blob = io_layer[key]
            parts.append(f"<h4>{html.escape(key)}</h4>")
            parts.append(
                "<pre style='white-space:pre-wrap;font-size:12px;background:#f6f6f8;padding:12px;border-radius:8px'>"
                f"{html.escape(json.dumps(blob, ensure_ascii=False, indent=2))}"
                "</pre>"
            )
    elif not nm:
        parts.append(
            "<p><em>Каталог io/ пуст или отсутствует; детальный разбор пропаганды/IO по файлам слоя недоступен.</em></p>"
        )

    return "".join(parts)


def build_timeline_html(nodes: list[dict], edges: list[dict]) -> str:
    if not nodes and not edges:
        return "<p><em>В артефактах нет событий временной шкалы (graph пуст).</em></p>"
    items: list[str] = []
    for n in nodes[:50]:
        if not isinstance(n, dict):
            continue
        label = html.escape(str(n.get("label") or n.get("id") or n.get("node_id") or ""))
        items.append(f"<li>{label}</li>")
    if len(nodes) > 50:
        items.append(f"<li><em>… и ещё {len(nodes) - 50} узлов (сокращено).</em></li>")
    return f'<ol class="timeline">{"".join(items)}</ol>'


def build_evidence_map_html(
    nodes: list[dict],
    edges: list[dict],
    waves: list[dict],
    evidence: list[dict],
) -> str:
    return (
        f"<p><strong>Graph:</strong> узлов {len(nodes)}, рёбер {len(edges)}; "
        f"<strong>waves:</strong> {len(waves)}; <strong>evidence cards:</strong> {len(evidence)}.</p>"
    )


def build_identity_resolution_html(nodes: list[dict]) -> str:
    if not nodes:
        return "<p><em>Нет сущностей в entity-registry / target-graph.</em></p>"
    rows: list[str] = []
    for n in nodes[:100]:
        if not isinstance(n, dict):
            continue
        nid = html.escape(str(n.get("id") or n.get("node_id") or ""))
        lab = html.escape(str(n.get("label") or n.get("name") or ""))
        typ = html.escape(str(n.get("type") or n.get("entity_type") or ""))
        rows.append(f"<tr><td>{nid}</td><td>{lab}</td><td>{typ}</td></tr>")
    return (
        "<table><thead><tr><th>id</th><th>label</th><th>type</th></tr></thead><tbody>"
        f"{''.join(rows)}</tbody></table>"
    )


def build_coverage_matrix_html(claims: list[dict], sources: list[dict]) -> str:
    return (
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>"
        f"<tr><td>claims_total</td><td>{len(claims)}</td></tr>"
        f"<tr><td>sources_total</td><td>{len(sources)}</td></tr>"
        "</tbody></table>"
    )


def build_evidence_excerpt_list_html(evidence: list[dict]) -> str:
    items: list[str] = []
    for e in evidence[:80]:
        if not isinstance(e, dict):
            continue
        eid = html.escape(str(e.get("evidence_id") or e.get("evidence_card_id") or ""))
        ex = e.get("extracted_fact_or_excerpt")
        text = ""
        if isinstance(ex, dict):
            text = str(ex.get("text") or ex.get("kind") or "")
        items.append(f"<li><strong>{eid}</strong> — {html.escape(text[:500])}</li>")
    if len(evidence) > 80:
        items.append(f"<li><em>… сокращено, всего карточек: {len(evidence)}</em></li>")
    return f"<ul>{''.join(items)}</ul>"


def build_proof_scripts_html(rd: Path, proofs: list[str]) -> str:
    scripts: list[str] = []
    for p in proofs:
        fp = rd / p
        if not fp.is_file():
            continue
        pid = p.replace("/", "-").replace(".", "-") + "-json"
        raw = fp.read_text(encoding="utf-8")
        safe_id = pid.replace('"', "")
        scripts.append(
            f'<script type="application/json" id="{html.escape(safe_id)}">'
            f"{html.escape(raw)}</script>"
        )
    return (
        "<section id=\"embedded-proof-blocks\"><h2>Embedded proof blocks</h2>"
        "<p>HTML не является proof сам по себе; валидаторы сверяют блоки с файлами run-dir.</p>"
        f"{''.join(scripts)}</section>"
    )


def build_standard_rfo_proof_blocks_html(rd: Path) -> str:
    """Emit ``<script type=\"application/json\" id=\"…\">`` blocks matching ``validate_html_proof_matches_runtime_artifacts``."""
    scripts: list[str] = []
    rd = Path(rd).resolve()
    for sid, rel in _RFO_BLOCK_TO_FILE:
        fp = rd / rel
        if not fp.is_file():
            continue
        raw = fp.read_text(encoding="utf-8")
        scripts.append(
            f'<script type="application/json" id="{html.escape(sid)}">'
            f"{html.escape(raw)}</script>"
        )
    extra_paths = [
        "run.json",
        "claims/claims-registry.json",
        "evidence/evidence-cards.json",
        "report/analytical-memo.json",
        "report/factual-dossier.json",
        "report/io-propaganda-check.json",
        "self-audit/runtime-self-audit.json",
    ]
    for p in extra_paths:
        fp = rd / p
        if not fp.is_file():
            continue
        pid = p.replace("/", "-").replace(".", "-") + "-json"
        raw = fp.read_text(encoding="utf-8")
        safe_id = pid.replace('"', "")
        scripts.append(
            f'<script type="application/json" id="{html.escape(safe_id)}">'
            f"{html.escape(raw)}</script>"
        )
    return (
        "<section id=\"embedded-proof-blocks\"><h2>Embedded proof blocks</h2>"
        "<p>MD-first HTML shell; JSON blocks mirror on-disk artifacts for validators.</p>"
        f"{''.join(scripts)}</section>"
    )


def md_to_html_body(md: str) -> str:
    """Render Markdown to an HTML fragment; safe fallback if ``markdown`` is not installed."""
    try:
        import markdown as _markdown  # type: ignore[import-not-found]

        return str(
            _markdown.markdown(
                md,
                extensions=["tables", "fenced_code", "nl2br"],
            )
        )
    except Exception:
        return (
            '<main class="rfo-md-fallback"><pre class="rfo-md-pre">'
            f"{html.escape(md)}"
            "</pre></main>"
        )


def build_full_report_html_from_markdown(rd: Path, md_text: str) -> str:
    """Standalone HTML document derived **only** from Markdown + standard proof blocks."""
    rd = Path(rd).resolve()
    run_meta = jr(rd / "run.json", {})
    run_id = str(run_meta.get("run_id") or "UNKNOWN")
    title = f"RFO Report — {run_id}"
    inner = md_to_html_body(md_text)
    proof = build_standard_rfo_proof_blocks_html(rd)
    styles = (
        "<style>body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#fafafa;color:#111}"
        ".rfo-from-md{max-width:1100px;margin:0 auto;padding:16px 20px 48px;background:#fff}"
        ".rfo-md-pre{white-space:pre-wrap;font-size:13px;font-family:ui-monospace,monospace}"
        "table{border-collapse:collapse;width:100%;margin:12px 0}"
        "th,td{border:1px solid #ccc;padding:6px;text-align:left}"
        "code{background:#f0f0f0;padding:1px 4px;border-radius:3px}</style>"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ru">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n{styles}\n</head>\n<body>\n"
        '<article class="rfo-from-md rfo-md-first">\n'
        f"{inner}\n</article>\n{proof}\n</body>\n</html>\n"
    )


def rebuild_canonical_md_then_html(rd: Path, *, source: str = "rebuild_canonical_md_then_html") -> tuple[bool, str]:
    """Write ``report/full-report.md`` from JSON, then ``report/full-report.html`` **only** from that MD."""
    rd = Path(rd).resolve()
    ok, note = minimal_report_sources_ready(rd)
    if not ok:
        return False, note
    try:
        inputs = ReportRunInputs.from_run_dir(rd)
        md_doc = build_full_report_md(inputs)
        if not md_doc.strip():
            return False, "empty_md"
        write_canonical_full_report_md(rd, md_doc, source=source)
    except Exception as exc:
        return False, f"md_write_failed:{exc!r}"
    try:
        html_doc = build_full_report_html_from_markdown(rd, md_doc)
        write_canonical_full_report_html(rd, html_doc, source=source)
    except Exception as exc:
        return False, f"html_failed_md_preserved:{exc!r}"
    return True, "md_then_html_ok"


def build_run_banner_html(
    rd: Path,
    provider: str,
    disclaimer: str,
    user_visible_research: bool,
    version: str,
) -> str:
    run_meta = jr(rd / "run.json", {})
    mode_s = html.escape(str(run_meta.get("mode", "unknown")))
    depth = "full sources" if user_visible_research else "seed/stub"
    banner_obj = {
        "rfo_run_mode": run_meta.get("mode"),
        "skill_version": version,
        "user_visible_research": user_visible_research,
        "note": (
            "Treat seed-only output as provisional until external gates pass. "
            "On-disk HTML completeness is not the same as user-visible delivery on a host channel (ADR-016)."
        ),
    }
    banner_json = html.escape(json.dumps(banner_obj, ensure_ascii=False))
    host_line_html = (
        " Compute-only artifact bundle; "
        "if a host forwards truncated text or attachments, compare with paths in "
        "<code>result-manifest.json</code> / handoff capsule."
    )
    return (
        "<header role=\"banner\" class=\"rfo-run-banner\" style=\"background:#37474f;color:#eceff1;padding:10px 14px;"
        "border-radius:6px;margin-bottom:14px;font-size:13px;line-height:1.45\">"
        "<strong>Research report</strong> · "
        f"run mode <code>{mode_s}</code> · evidence depth: {html.escape(depth)}."
        f"{host_line_html}"
        f"</header><script type=\"application/json\" id=\"rfo-run-mode-banner\">{banner_json}</script>"
    )


def build_feature_truth_capabilities_html(rd: Path) -> str:
    """Small read-only excerpt from ``feature-truth-matrix.json`` (no invented capabilities)."""
    ftm = jr(rd / "feature-truth-matrix.json", {})
    feats = ftm.get("features") if isinstance(ftm.get("features"), dict) else {}
    if not feats:
        return ""
    prio = (
        "real_external_search_workers",
        "external_user_visible_delivery_via_skill",
        "work_unit_decomposition",
        "relay_prefetch_bridge",
        "citation_grounding",
    )
    keys: list[str] = []
    for k in prio:
        if k in feats and k not in keys:
            keys.append(k)
    for k in sorted(feats.keys()):
        if k not in keys:
            keys.append(k)
        if len(keys) >= 12:
            break
    rows: list[str] = []
    for k in keys[:12]:
        v = feats.get(k)
        rows.append(
            f"<dt><code>{html.escape(k)}</code></dt>"
            f"<dd><code>{html.escape(json.dumps(v, ensure_ascii=False)[:280])}</code></dd>"
        )
    caps_json = html.escape(json.dumps({"features_subset": {k: feats[k] for k in keys[:12]}}, ensure_ascii=False))
    return (
        "<aside class=\"rfo-capabilities-truth\" style=\"margin:10px 0 14px;padding:8px 12px;"
        "border-left:4px solid #546e7a;background:#fafafa;font-size:12px;line-height:1.4\">"
        "<strong>Capabilities (truth matrix excerpt)</strong> — scaffold values reflect validator truth, "
        "not marketing copy.<dl style=\"margin:6px 0 0;padding:0\">"
        f"{''.join(rows)}"
        "</dl></aside>"
        f"<script type=\"application/json\" id=\"rfo-feature-truth-excerpt\">{caps_json}</script>"
    )


def build_full_report_html(
    rd: Path,
    task: str,
    run_id: str,
    job_id: str,
    cmd_id: str,
    provider: str,
    memo: dict,
    claims: list[dict],
    sources: list[dict],
    evidence: list[dict],
    waves: list[dict],
    nodes: list[dict],
    edges: list[dict],
    io: dict,
    audit: dict,
    disclaimer: str,
    user_visible_research: bool,
    factual: dict,
    generated_at: str,
    version: str,
) -> str:
    idx = build_source_index(sources)
    io_layer = load_io_layer_files(rd)

    key_verdict = html.escape(str(memo.get("executive_summary") or disclaimer))
    gaps = memo.get("data_gaps")
    gap_html = ""
    if isinstance(gaps, list) and gaps:
        gap_html = "<ul>" + "".join(f"<li>{html.escape(str(g))}</li>" for g in gaps) + "</ul>"
    else:
        gap_html = "<p><em>Нет явных записей data_gaps.</em></p>"

    exec_summary = (
        f"<p class=\"section-summary\">{html.escape(str(memo.get('executive_summary') or ''))}</p>"
        f"<p><strong>Заголовок:</strong> {html.escape(str(memo.get('title') or ''))}</p>"
        f"<p><strong>Уверенность (memo):</strong> <code>{html.escape(str(memo.get('confidence') or ''))}</code></p>"
        "<h3>Data gaps</h3>"
        f"{gap_html}"
    )

    search_quality = audit.get("search_quality") if isinstance(audit, dict) else {}
    search_strategy = (
        "<p>"
        + html.escape(json.dumps(search_quality, ensure_ascii=False) if search_quality else "{}")
        + "</p>"
    )

    source_quality_io = io_layer.get("source_laundering_map")
    if source_quality_io is not None:
        source_quality = (
            "<pre style='white-space:pre-wrap'>"
            f"{html.escape(json.dumps(source_quality_io, ensure_ascii=False, indent=2))}"
            "</pre>"
        )
    else:
        source_quality = "<p><em>source-laundering-map.json отсутствует или пуст.</em></p>"

    deviations = audit.get("deviations") if isinstance(audit, dict) else []
    dev_html = (
        "<ul>"
        + "".join(f"<li>{html.escape(json.dumps(d, ensure_ascii=False))}</li>" for d in deviations or [])
        + "</ul>"
    )
    if not deviations:
        dev_html = "<p><em>Отклонений не зафиксировано.</em></p>"

    validation_proof = (
        f"<p>run_id: {html.escape(run_id)} · job_id: {html.escape(job_id)} · "
        f"command_id: {html.escape(cmd_id)} · skill_version: {html.escape(version)}</p>"
        f"<p>Factual dossier: claims={factual.get('claims_total')}, "
        f"sources={factual.get('sources_total')}, evidence_cards={factual.get('evidence_cards_total')}</p>"
    )

    completion_proof = jr(rd / "validation-transcript.json", {})
    pkg_manifest = jr(rd / "research-package-manifest.json", {})

    mapping: dict[str, str] = {
        "TITLE": html.escape(f"RFO Report — {run_id}"),
        "GENERATED_AT": html.escape(generated_at),
        "OUTPUT_PROFILE": "v19 investigation / wiki-citations",
        "RUN_BANNER": (
            build_run_banner_html(rd, provider, disclaimer, user_visible_research, version)
            + build_feature_truth_capabilities_html(rd)
        ),
        "EXECUTIVE_SUMMARY": exec_summary,
        "KEY_VERDICT": f"<div class=\"callout info\"><strong>Key verdict:</strong> {key_verdict}</div>",
        "RESEARCH_QUESTION_SCOPE": f"<p>{html.escape(task)}</p>",
        "METHODOLOGY": (
            "<p>Детерминированная сборка отчёта из JSON артефактов run-dir (RFO v19). "
            "Доменный вывод не генерируется Python-кодом — только данные из файлов; "
            "пустые разделы помечены явно.</p>"
        ),
        "SEARCH_STRATEGY": search_strategy,
        "SOURCE_QUALITY": source_quality,
        "IO_PROPAGANDA_AND_NARRATIVE": build_io_propaganda_html(io, io_layer),
        "EVIDENCE_MAP": build_evidence_map_html(nodes, edges, waves, evidence)
        + "<h3>Evidence excerpts</h3>"
        + build_evidence_excerpt_list_html(evidence),
        "VERIFIED_CLAIMS": render_claim_cards_html(claims, idx, "verified"),
        "UNCERTAIN_CLAIMS": render_claim_cards_html(claims, idx, "nonverified"),
        "FACT_CHECK": "<p><em>Факт-чек как отдельный слой: статусы отражены в карточках claims выше.</em></p>",
        "CITATION_LOCATOR": (
            "<p>Inline маркеры <code>[n]</code> ведут на <code>#ref-n</code> в списке References.</p>"
        ),
        "ADVERSARIAL_REVIEW": (
            f"<p><strong>IO verdict (summary):</strong> <code>{html.escape(str(io.get('verdict')))}</code></p>"
            "<p><em>Расширенный контраргументный слой — при наличии данных в артефактах.</em></p>"
        ),
        "ERROR_AUDIT": dev_html,
        "KNOWN_GAPS": gap_html,
        "COVERAGE_MATRIX": build_coverage_matrix_html(claims, sources),
        "SOURCE_ROWS_WITH_FULL_URLS": render_source_table_rows(sources),
        "IDENTITY_RESOLUTION": build_identity_resolution_html(nodes),
        "VALIDATION_PROOF": validation_proof,
        "COMPLETION_PROOF_JSON": html.escape(json.dumps(completion_proof, ensure_ascii=False)),
        "RESEARCH_PACKAGE_MANIFEST_JSON": html.escape(json.dumps(pkg_manifest, ensure_ascii=False)),
        "APPENDICES": (
            f"<p>Waves: {len(waves)}</p><pre style='white-space:pre-wrap;font-size:12px'>"
            f"{html.escape(json.dumps(waves[:20], ensure_ascii=False, indent=2))}"
            "</pre>"
        ),
        "WIKI_REFERENCES": render_wiki_references(sources, idx),
        "TIMELINE": build_timeline_html(nodes, edges),
        "COMPETING_HYPOTHESES": "<p><em>Гипотезы не материализованы в отдельном JSON — секция-заготовка.</em></p>",
        "FORECAST": "<p><em>Прогноз не материализован в артефактах.</em></p>",
        "RISKS_AND_EFFECTS": "<p><em>Риски второго порядка — см. Known Gaps и audit.</em></p>",
    }

    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    filled = fill_template(tpl, mapping)

    proofs = [
        "run.json",
        "entrypoint-proof.json",
        "runtime-status.json",
        "claims/claims-registry.json",
        "evidence/evidence-cards.json",
        "report/analytical-memo.json",
        "report/factual-dossier.json",
        "report/io-propaganda-check.json",
        "report/semantic-report.json",
        "self-audit/runtime-self-audit.json",
        "delivery-manifest.json",
        "final-answer-gate.json",
    ]
    proof_html = build_proof_scripts_html(rd, proofs)

    if "</body>" in filled:
        return filled.replace("</body>", proof_html + "\n</body>", 1)
    return filled + proof_html


def build_full_report_html_from_run_dir(rd: Path) -> str:
    """Rebuild HTML from an existing run directory using the **legacy** wiki template (JSON → template).

    For the canonical MD-first pipeline use ``rebuild_canonical_md_then_html`` / ``build_full_report_html_from_markdown``.
    """
    inputs = ReportRunInputs.from_run_dir(rd)
    from runtime.status import VERSION
    from runtime.util import now as util_now

    return build_full_report_html(
        rd=inputs.rd,
        task=inputs.task,
        run_id=inputs.run_id,
        job_id=inputs.job_id,
        cmd_id=inputs.cmd_id,
        provider=inputs.provider,
        memo=inputs.memo,
        claims=inputs.claims,
        sources=inputs.sources,
        evidence=inputs.evidence,
        waves=inputs.waves,
        nodes=inputs.nodes,
        edges=inputs.edges,
        io=inputs.io,
        audit=inputs.audit,
        disclaimer=inputs.disclaimer,
        user_visible_research=inputs.user_visible_research,
        factual=inputs.factual,
        generated_at=util_now(),
        version=VERSION,
    )


def sniff_html_document(head: str) -> str:
    """Coarse format profile from the first bytes of a file (utf-8 text).

    Returns one of: html_document, html_fragment, markdown_like, empty, unknown.
    """
    if not head:
        return "empty"
    text = head.lstrip("\ufeff \t\n\r")
    if not text.strip():
        return "empty"
    sample = text[:8192]
    low = sample.lower()
    if low.startswith("<!doctype html") or low.startswith("<html"):
        return "html_document"
    if "<?xml" in low[:200] and "html" in low[:1200]:
        return "html_document"
    if "<html" in sample[:2000]:
        return "html_document"
    if any(tag in low[:4000] for tag in ("<body", "<head", "<article", "<main", "<div class=", "<section")):
        return "html_fragment"
    line0 = sample.splitlines()[0].strip() if sample.splitlines() else ""
    if line0.startswith("#") or line0.startswith("|") or line0.startswith("##"):
        return "markdown_like"
    if "\n# " in sample[:2500] or sample.lstrip().startswith("# "):
        return "markdown_like"
    if "<p>" in low[:2000] or "<h1" in low[:2000] or "<table" in low[:2000]:
        return "html_fragment"
    return "unknown"


def content_profile_for_manifest(sniff: str) -> str:
    """Derived manifest hint: html_v1 = suitable standalone HTML; else non-html prose risk."""
    if sniff in ("html_document", "html_fragment"):
        return "html_v1"
    if sniff == "empty":
        return "empty"
    if sniff == "markdown_like":
        return "markdown_like"
    return "unknown"


def write_canonical_full_report_html(rd: Path, html_doc: str, *, source: str = "unknown") -> Path:
    """Single choke-point for writes to ``report/full-report.html`` (creates ``report/``)."""
    _ = source  # reserved for tracing / debugging
    p = rd.resolve() / FULL_REPORT_REL
    tw(p, html_doc)
    return p


def _try_rebuild_full_report_html(rd: Path) -> tuple[bool, str]:
    """Rebuild canonical dossier: ``report/full-report.md`` then ``report/full-report.html`` from MD only."""
    return rebuild_canonical_md_then_html(rd, source="ensure_canonical_full_report_html")


def ensure_canonical_full_report_html(rd: Path) -> tuple[bool, str]:
    """Ensure ``report/full-report.md`` exists and ``report/full-report.html`` is HTML-ish (MD-first).

    When either is missing or HTML is corrupt, rebuild via ``rebuild_canonical_md_then_html`` when core
    JSON exists. If HTML rendering fails after MD was written, returns ``(True, "md_only;…")``.
    """
    rd = Path(rd).resolve()
    fp = rd / FULL_REPORT_REL
    md_p = rd / FULL_REPORT_MD_REL
    md_ok = md_p.is_file() and md_p.stat().st_size > 32

    html_ok = False
    prof = "missing_file"
    if fp.is_file():
        raw = fp.read_bytes()[:8192].decode("utf-8", errors="replace")
        prof = sniff_html_document(raw)
        html_ok = prof in ("html_document", "html_fragment")

    if html_ok and md_ok:
        return True, prof

    ok, msg = rebuild_canonical_md_then_html(rd, source="ensure_canonical_full_report_html")
    if ok:
        return True, f"repaired_or_synced:{prof if fp.is_file() else 'missing_html_before'}:{msg}"
    if msg.startswith("html_failed_md_preserved:") and md_p.is_file() and md_p.stat().st_size > 32:
        return True, f"md_only;{msg}"
    return False, msg
