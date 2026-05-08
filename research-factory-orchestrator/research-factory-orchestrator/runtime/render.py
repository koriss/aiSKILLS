"""Deterministic artifact rendering for RFO run directories."""
from __future__ import annotations

import html
import json
from pathlib import Path

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
    jw(rd / "chat/chat-message-plan.json", {"run_id": run_id, "job_id": job_id, "provider": provider, "messages": []})

    tw(rd / "chat/message-001-analytical-memo.txt", f"{memo['title']}\n{memo['executive_summary']}\n")
    tw(rd / "chat/message-002-facts.txt", f"Claims: {len(cs)}\nSources: {len(sources)}\nEvidence: {len(evidence)}\n")
    tw(rd / "chat/message-003-io-propaganda-check.txt", f"IO verdict: {io['verdict']}\n")
    tw(rd / "chat/message-004-files.txt", "Files prepared; external delivery must be proven by delivery-manifest/ACK.\n")

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

    def sec(title: str, body: str) -> str:
        return f"<section><h2>{html.escape(title)}</h2>{body}</section>"

    claim_items = "".join(
        f"<li><b>{html.escape(str(c.get('claim_id', 'n/a')))}</b> {html.escape(str(c.get('claim_text') or c.get('text') or ''))}</li>"
        for c in cs
    ) or "<li>no claims</li>"
    source_items = "".join(
        f"<li>{html.escape(str(s.get('source_id', 'n/a')))} — {html.escape(str(s.get('title', '')))}</li>"
        for s in sources
    ) or "<li>no sources</li>"
    evidence_items = "".join(
        f"<li>{html.escape(str(e.get('evidence_id') or e.get('evidence_card_id') or 'n/a'))}</li>" for e in evidence
    ) or "<li>no evidence cards</li>"

    body = (
        sec("Analytical memo", f"<p>{html.escape(memo['executive_summary'])}</p>")
        + sec("Claims", f"<ul>{claim_items}</ul>")
        + sec("Sources", f"<ul>{source_items}</ul>")
        + sec("Evidence cards", f"<ul>{evidence_items}</ul>")
        + sec("Wave graph", f"<p>waves loaded: {len(waves)}</p>")
        + sec("Self audit", f"<p>{html.escape(disclaimer)}</p>")
    )
    proofs = [
        "run.json",
        "entrypoint-proof.json",
        "runtime-status.json",
        "claims/claims-registry.json",
        "evidence/evidence-cards.json",
        "report/analytical-memo.json",
        "report/factual-dossier.json",
        "report/io-propaganda-check.json",
        "self-audit/runtime-self-audit.json",
        "delivery-manifest.json",
        "final-answer-gate.json",
    ]
    scripts = "".join(
        f"<script type='application/json' id='{p.replace('/', '-').replace('.', '-')}-json'>{html.escape((rd / p).read_text(encoding='utf-8'))}</script>"
        for p in proofs
        if (rd / p).exists()
    )
    run_meta = jr(rd / "run.json", {})
    mode_s = html.escape(str(run_meta.get("mode", "unknown")))
    prov_s = html.escape(str(provider or ""))
    banner_obj = {
        "rfo_run_mode": run_meta.get("mode"),
        "provider": provider,
        "skill_version": VERSION,
        "user_visible_research": user_visible_research,
        "note": "Smoke/seed/stub runs must not read as production research until gates pass.",
    }
    banner_json = html.escape(json.dumps(banner_obj, ensure_ascii=False))
    banner_html = (
        f"<header role='banner' style='background:#1a237e;color:#fff;padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:14px'><strong>RFO run-mode banner</strong> · mode=<code>{mode_s}</code> · provider=<code>{prov_s}</code> · user_visible_research={str(user_visible_research).lower()} · {html.escape(disclaimer)}</header>"
        f"<script type='application/json' id='rfo-run-mode-banner'>{banner_json}</script>"
    )
    tw(
        rd / "report/full-report.html",
        f"<!DOCTYPE html><html lang='ru'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>RFO v19 Internal Analysis Report</title><style>body{{font-family:Arial,sans-serif;line-height:1.55;max-width:1100px;margin:0 auto;padding:24px;background:#f7f7f9;color:#111}}section{{background:white;border:1px solid #ddd;border-radius:10px;padding:18px;margin:14px 0}}h1,h2{{color:#17213a}}</style></head><body>{banner_html}<h1>Research Factory Orchestrator v19 — Internal Analysis/Audit Report</h1><p>run_id: {html.escape(run_id)} · job_id: {html.escape(job_id)} · skill_version: {html.escape(VERSION)}</p>{body}<section><h2>Embedded proof blocks</h2><p>HTML не является proof сам по себе; валидаторы сверяют blocks с файлами run-dir.</p>{scripts}</section></body></html>",
    )
    artifact_layout = {
        "schema_version": "v19.0",
        "run_id": run_id,
        "skill_version": VERSION,
        "layout": "v19-dual",
        "root_artifacts": [
            "claims-registry.json",
            "sources.json",
            "evidence-cards.json",
            "report/full-report.html",
        ],
        "subdir_artifacts": [
            "claims/claims-registry.json",
            "sources/sources.json",
            "evidence/evidence-cards.json",
        ],
        "note": "v19 runtime emits canonical copies at run-dir root and keeps subdir copies for compatibility.",
    }
    jw(rd / "artifact-layout.json", artifact_layout)
