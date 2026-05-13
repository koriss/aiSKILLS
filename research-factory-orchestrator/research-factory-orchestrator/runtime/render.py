"""Deterministic artifact rendering for RFO run directories."""
from __future__ import annotations

import json
from pathlib import Path

from runtime.chat_md import (
    apply_facts_gate,
    build_analysis_markdown,
    build_facts_markdown,
    compute_quality_metadata,
)
from runtime.report_html import build_full_report_html_from_markdown, write_canonical_full_report_html
from runtime.report_inputs import ReportRunInputs
from runtime.report_md import build_full_report_md, write_canonical_full_report_md
from runtime.status import VERSION
from runtime.util import jr, jw, now, sid, slug, tw


def allocate(runs_root, task, provider, interface):
    label = f"{slug(task)}_{now().replace('-', '').replace(':', '').replace('Z', '')[:15]}"
    run_id = sid("RUN", label, task)
    job_id = sid("JOB", run_id, task)
    cmd_id = sid("CMD", run_id, task)
    run_dir = Path(runs_root) / "runs" / label
    run_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_id": run_id,
        "job_id": job_id,
        "command_id": cmd_id,
        "run_label": label,
        "run_dir": str(run_dir),
        "task": task,
        "provider": provider,
        "interface": interface,
        "created_at": now(),
        "version": VERSION,
    }
    jw(run_dir / "run-catalog-entry.json", entry)
    idx = Path(runs_root) / "index"
    idx.mkdir(parents=True, exist_ok=True)
    idx.joinpath("runs-index.jsonl").open("a", encoding="utf-8").write(json.dumps(entry, ensure_ascii=False) + "\n")
    jw(idx / "latest.json", entry)
    return entry


def _load_json(path: Path, default):
    data = jr(path, default)
    return data if isinstance(data, type(default)) else default


def _load_claims(rd: Path) -> list[dict]:
    data = _load_json(rd / "claims-registry.json", {})
    claims = data.get("claims") if isinstance(data, dict) else []
    return claims if isinstance(claims, list) else []


def _load_sources(rd: Path) -> list[dict]:
    data = _load_json(rd / "sources.json", {})
    items = data.get("sources") if isinstance(data, dict) else []
    return items if isinstance(items, list) else []


def _load_evidence(rd: Path) -> list[dict]:
    data = _load_json(rd / "evidence-cards.json", {})
    items = data.get("evidence_cards") if isinstance(data, dict) else []
    return items if isinstance(items, list) else []


def _load_graph(rd: Path) -> tuple[list[dict], list[dict]]:
    graph = _load_json(rd / "graph/target-graph.json", {})
    nodes = graph.get("nodes") if isinstance(graph, dict) else []
    edges = graph.get("edges") if isinstance(graph, dict) else []
    return (nodes if isinstance(nodes, list) else [], edges if isinstance(edges, list) else [])


def _load_waves(rd: Path) -> list[dict]:
    graph = _load_json(rd / "graph/wave-plan.json", {})
    waves = graph.get("waves") if isinstance(graph, dict) else []
    return waves if isinstance(waves, list) else []


def _seed_only_mode(rd: Path) -> bool:
    c = _load_json(rd / "collection-result.json", {})
    return bool(isinstance(c, dict) and c.get("seed_only") is True)


def _source_body_for_claim(src: dict) -> str:
    """Derive claim text from a source row; tolerate missing fetched body."""
    cs = str(src.get("content_snippet") or src.get("content") or "").strip()
    if cs:
        return cs[:500]
    title = str(src.get("title") or "").strip()
    url = str(src.get("url") or src.get("canonical_origin_id") or "").strip()
    parts: list[str] = []
    if title:
        parts.append(title)
    if url:
        parts.append(url)
    err = str(src.get("content_fetch_error") or src.get("content_error") or "").strip()
    if err:
        parts.append(f"[fetch: {err[:120]}]")
    body = " ".join(parts).strip()
    return body[:500] if body else "(no extractable text)"


def _conf_bucket_for_evidence(conf: float) -> str:
    if conf >= 0.85:
        return "high"
    if conf >= 0.6:
        return "medium"
    return "low"


def hydrate_claims_if_needed(rd: Path, task: str, *, run_id: str | None = None) -> bool:
    """If external sources exist but claims-registry is empty, synthesize v19 claims + evidence.

    Ensures citation grounding and downstream validators see non-empty claims when
    ``sources.json`` already lists externally collected rows (relay packet, seeds, etc.).
    Writes ``meta.origin=hydrate_from_sources`` on synthetic claims for disclosure.
    """
    rd = Path(rd)
    if _seed_only_mode(rd):
        return False
    cs = _load_claims(rd)
    if cs:
        return False
    sources = _load_sources(rd)
    external = [
        s
        for s in sources
        if isinstance(s, dict)
        and s.get("source_role") != "seed"
        and not str(s.get("source_id") or "").startswith("stub:")
    ]
    if not external:
        return False
    rid = run_id or ""
    if not rid:
        run_payload = _load_json(rd / "run.json", {})
        rid = str(run_payload.get("run_id") or rd.name)

    v19_claims: list[dict] = []
    evidence_cards: list[dict] = []
    for i, src in enumerate(external):
        body = _source_body_for_claim(src)
        src_id = str(src.get("source_id") or f"SRC-HYDR-{i+1:03d}")
        claim_id = f"C-HYDR-{i+1:03d}"
        ev_id = f"EV-HYDR-{i+1:03d}"
        vm = src.get("verification_mode")
        status_v19 = "reported_claim" if vm == "raw_document" else "inferred_assessment"
        conf_f = 0.88 if vm == "raw_document" else 0.72
        v19_claims.append(
            {
                "claim_id": claim_id,
                "claim_text": body,
                "claim_type": "source_derived",
                "status": status_v19,
                "confidence": _conf_bucket_for_evidence(conf_f),
                "evidence_card_ids": [ev_id],
                "support_set": [
                    {
                        "source_id": src_id,
                        "evidence_card_id": ev_id,
                        "role_for_claim": "primary_support",
                    }
                ],
                "meta": {"synthetic": True, "origin": "hydrate_from_sources"},
            }
        )
        evidence_cards.append(
            {
                "evidence_id": ev_id,
                "source_ids": [src_id],
                "claim_ids": [claim_id],
                "extracted_fact_or_excerpt": {"kind": "excerpt", "text": body[:400]},
                "supports": "direct",
                "confidence": _conf_bucket_for_evidence(conf_f),
            }
        )

    bundle = {"schema_version": "v19.0", "claims": v19_claims}
    ev_bundle = {"schema_version": "v19.0", "evidence_cards": evidence_cards}
    jw(rd / "claims-registry.json", bundle)
    jw(rd / "claims/claims-registry.json", {"run_id": rid, "taxonomy_version": "v19.2", "claims": v19_claims})
    jw(rd / "evidence-cards.json", ev_bundle)
    jw(rd / "evidence/evidence-cards.json", {"run_id": rid, "evidence_cards": evidence_cards})
    return True


def render_all(rd, task, run_id, job_id, cmd_id, provider):
    cs = _load_claims(rd)
    sources = _load_sources(rd)
    evidence = _load_evidence(rd)
    nodes, edges = _load_graph(rd)
    waves = _load_waves(rd)

    seed_only = _seed_only_mode(rd)
    external_source_count = sum(
        1
        for s in sources
        if isinstance(s, dict)
        and s.get("source_role") != "seed"
        and not str(s.get("source_id") or "").startswith("stub:")
    )
    user_visible_research = external_source_count > 0
    disclaimer = (
        "No external evidence collected; runtime structure only."
        if not user_visible_research
        else "External evidence present."
    )

    if seed_only and not cs:
        cs = [
            {
                "claim_id": "stub:seed-only",
                "claim_text": "No externally collected claims for this seed-only run.",
                "claim_type": "inferred_assessment",
                "status": "insufficient_evidence",
                "confidence": "low",
                "evidence_card_ids": ["stub:seed-only"],
                "support_set": [
                    {
                        "source_id": "stub:seed-only",
                        "evidence_card_id": "stub:seed-only",
                        "role_for_claim": "context",
                    }
                ],
                "meta": {"synthetic": True, "origin": "seed_only_stub"},
            }
        ]
    if seed_only and not evidence:
        evidence = [
            {
                "evidence_id": "stub:seed-only",
                "source_ids": ["stub:seed-only"],
                "claim_ids": ["stub:seed-only"],
                "evidence_type": "other",
                "extracted_fact_or_excerpt": {
                    "kind": "extracted_fact",
                    "text": "Seed-only run generated no external evidence.",
                },
                "supports": "contextual",
                "confidence": "low",
            }
        ]

    cs, facts_gate_meta = apply_facts_gate(cs, sources)
    jw(rd / "report/facts-gate-meta.json", facts_gate_meta)

    claims_bundle = {"schema_version": "v19.0", "claims": cs}
    evidence_bundle = {"schema_version": "v19.0", "evidence_cards": evidence}
    sources_bundle = {"schema_version": "v19.0", "sources": sources}

    # Keep root/subdir compatibility while preserving v19 schema at root.
    jw(rd / "claims-registry.json", claims_bundle)
    jw(rd / "evidence-cards.json", evidence_bundle)
    jw(rd / "sources.json", sources_bundle)
    jw(rd / "claims/claims-registry.json", {"run_id": run_id, "claims": cs})
    jw(rd / "sources/sources.json", {"run_id": run_id, "sources": sources})
    jw(rd / "evidence/evidence-cards.json", {"run_id": run_id, "evidence_cards": evidence})
    jw(rd / "graph/entity-registry.json", {"run_id": run_id, "entities": nodes})
    jw(rd / "graph/edge-ledger.json", {"run_id": run_id, "edges": edges})
    jw(rd / "graph/wave-plan.json", {"run_id": run_id, "waves": waves})

    memo = {
        "run_id": run_id,
        "title": "Аналитическая записка",
        "executive_summary": disclaimer,
        "confidence": "low" if not user_visible_research else "medium",
        "data_gaps": [] if user_visible_research else ["external evidence missing"],
    }
    factual = {
        "run_id": run_id,
        "claims_total": len(cs),
        "sources_total": len(sources),
        "evidence_cards_total": len(evidence),
    }
    io = {
        "run_id": run_id,
        "method_matches": [],
        "narrative_map": [],
        "verdict": "insufficient_external_data" if not user_visible_research else "pending_manual_review",
    }
    audit = {
        "run_id": run_id,
        "deviations": [],
        "search_quality": {"external_search_executed": user_visible_research, "note": disclaimer},
        "tool_failures": [],
    }

    jw(rd / "report/analytical-memo.json", memo)
    jw(rd / "report/factual-dossier.json", factual)
    jw(rd / "report/io-propaganda-check.json", io)
    jw(rd / "self-audit/runtime-self-audit.json", audit)
    (rd / "chat").mkdir(parents=True, exist_ok=True)
    analysis_md = build_analysis_markdown(
        memo, io, disclaimer, user_visible_research, rd
    )
    facts_md = build_facts_markdown(cs, sources)
    tw(rd / "chat/01-analysis.md", analysis_md)
    tw(rd / "chat/02-facts.md", facts_md)

    qmeta = compute_quality_metadata(rd, seed_only, facts_gate_meta, cs, sources)
    jw(rd / "report/quality-metadata.json", qmeta)

    jw(
        rd / "chat/chat-message-plan.json",
        {
            "run_id": run_id,
            "job_id": job_id,
            "provider": provider,
            "plain_text_only": True,
            "mobile_safe": True,
            "no_tables": True,
            "no_local_paths": True,
            "no_premature_delivery_claims": True,
            "split_policy": {"max_message_chars": 3500, "logical_blocks": True},
            "delivery_claim_policy": {"may_claim_files_delivered": False},
            "messages": [
                {
                    "message_id": "message-001",
                    "id": "message-001",
                    "kind": "analysis",
                    "path": "chat/01-analysis.md",
                    "contains_delivery_claim": False,
                },
                {
                    "message_id": "message-002",
                    "id": "message-002",
                    "kind": "facts_with_links",
                    "path": "chat/02-facts.md",
                    "contains_delivery_claim": False,
                },
            ],
            "attachments": [
                {"event_id": "OUT-0005", "kind": "html_report", "path": "report/full-report.html"},
                {"event_id": "OUT-0006", "kind": "research_package", "path": "package/research-package.zip"},
            ],
        },
    )

    semantic = {
        "run_id": run_id,
        "claims": cs,
        "sources": sources,
        "evidence_cards": evidence,
        "memo": memo,
        "io_summary": io,
        "generated_at": now(),
    }
    jw(rd / "report/semantic-report.json", semantic)

    inputs = ReportRunInputs.from_run_dir(rd)
    md_doc = build_full_report_md(inputs)
    write_canonical_full_report_md(rd, md_doc, source="render_all")
    html_doc = build_full_report_html_from_markdown(rd, md_doc)
    write_canonical_full_report_html(rd, html_doc, source="render_all")
    artifact_layout = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "skill_version": VERSION,
        "layout": "v19-dual",
        "root_artifacts": [
            "claims-registry.json",
            "sources.json",
            "evidence-cards.json",
            "report/full-report.md",
            "report/full-report.html",
            "chat/01-analysis.md",
            "chat/02-facts.md",
        ],
        "subdir_artifacts": [
            "claims/claims-registry.json",
            "sources/sources.json",
            "evidence/evidence-cards.json",
        ],
        "note": "v19 runtime emits canonical copies at run-dir root and keeps subdir copies for compatibility.",
    }
    jw(rd / "artifact-layout.json", artifact_layout)
