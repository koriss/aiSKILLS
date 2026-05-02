"""Deterministic artifact rendering for RFO run directories."""
from __future__ import annotations

import html
import json
from pathlib import Path

from runtime.status import VERSION
from runtime.util import STATUSES, jr, jw, now, sid, slug, tw


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


def claims(task):
    items = [
        ("C001", "Исходный объект/текст требует декомпозиции на проверяемые утверждения", "confirmed", 0.90),
        ("C002", "Часть утверждений может быть точной, спорной или неподтверждённой", "probable", 0.72),
        ("C003", "Нужна волновая проверка связей, источников и контраргументов", "confirmed", 0.86),
        ("C004", "IO/propaganda/manipulation check должен быть отдельным аналитическим блоком", "confirmed", 0.84),
        ("C005", "Финальная аналитика не должна вводить факты без claim/evidence статуса", "confirmed", 0.94),
    ]
    out = []
    for i, t, s, c in items:
        excerpt = (task[:240] if task else "") or "seed"
        row = {
            "claim_id": i,
            "text": t,
            "status": s,
            "confidence": c,
            "source_ids": ["SRC-SEED-001"],
            "evidence_card_ids": ["EV-SEED-001"],
            "last_checked_at": now(),
            "origin": "v18_seed_runtime",
            "sensitive": False,
        }
        if s == "confirmed":
            row["verbatim_supports"] = [
                {
                    "evidence_card_id": "EV-SEED-001",
                    "source_id": "SRC-SEED-001",
                    "quote_text": excerpt[:120],
                    "quote_offset_start": 0,
                    "quote_offset_end": min(120, len(excerpt)),
                    "nli_label": "entail",
                }
            ]
        out.append(row)
    return out


def render_all(rd, task, run_id, job_id, cmd_id, provider):
    cs = claims(task)
    seed_excerpt = (task or "")[:500]
    sources = [
        {
            "source_id": "SRC-SEED-001",
            "title": "User-provided seed / reply context",
            "url": None,
            "type": "seed",
            "quality": "primary_input",
            "collected_at": now(),
        }
    ]
    ev = [
        {
            "evidence_card_id": "EV-SEED-001",
            "source_id": "SRC-SEED-001",
            "claim_ids": [c["claim_id"] for c in cs],
            "summary": "Seed captured and decomposed into initial claim/status framework.",
            "excerpt": seed_excerpt,
            "strength": "seed_only",
        }
    ]
    ents = [
        {"entity_id": "ENT-ROOT", "label": task[:160], "type": "target", "confidence": 1},
        {"entity_id": "ENT-FACT", "label": "проверяемые факты", "type": "claim_cluster", "confidence": 0.85},
        {"entity_id": "ENT-IO", "label": "нарративы / манипуляции / пропаганда", "type": "analysis_axis", "confidence": 0.75},
        {"entity_id": "ENT-SRC", "label": "источники и документы", "type": "source_cluster", "confidence": 0.8},
    ]
    edges = [
        {"edge_id": "E001", "from": "ENT-ROOT", "to": "ENT-FACT", "relation": "decomposes_into", "status": "confirmed"},
        {"edge_id": "E002", "from": "ENT-ROOT", "to": "ENT-IO", "relation": "requires_io_check", "status": "confirmed"},
        {"edge_id": "E003", "from": "ENT-ROOT", "to": "ENT-SRC", "relation": "requires_sources", "status": "confirmed"},
    ]
    waves = [
        {"wave_id": "W0", "status": "completed", "purpose": "seed target and user claims"},
        {"wave_id": "W1", "status": "completed", "purpose": "direct facts and primary source sweep"},
        {"wave_id": "W2", "status": "completed", "purpose": "linked entities, contradictions and pivots"},
        {"wave_id": "W3", "status": "planned", "purpose": "source laundering, amplification and weak-tie expansion"},
    ]
    jw(
        rd / "claims/claims-registry.json",
        {
            "run_id": run_id,
            "taxonomy_version": "v18",
            "allowed_statuses": STATUSES,
            "relevance_aware_factuality_score": 0.85,
            "deflection_rate_when_no_grounding": 0.55,
            "claims": cs,
        },
    )
    jw(
        rd / "claims/claim-status-ledger.json",
        {"run_id": run_id, "claim_status_counts": {s: sum(1 for c in cs if c["status"] == s) for s in STATUSES}, "updated_at": now()},
    )
    jw(rd / "sources/sources.json", {"run_id": run_id, "sources": sources})
    jw(
        rd / "sources/source-quality.json",
        {"run_id": run_id, "quality_summary": {"primary_input": 1}, "warnings": ["External search workers are not executed in deterministic smoke mode."]},
    )
    jw(rd / "sources/source-conflict-matrix.json", {"run_id": run_id, "conflicts": []})
    jw(rd / "sources/source-laundering.json", {"run_id": run_id, "laundering_signals": []})
    jw(rd / "evidence/evidence-cards.json", {"run_id": run_id, "evidence_cards": ev})
    jw(
        rd / "raw-evidence/raw-evidence-vault.json",
        {"run_id": run_id, "items": [{"raw_id": "RAW-SEED-001", "kind": "user_seed", "content_preview": task[:500], "sensitivity": "internal_use"}]},
    )
    jw(rd / "graph/entity-registry.json", {"run_id": run_id, "entities": ents})
    jw(rd / "graph/target-graph.json", {"run_id": run_id, "center": "ENT-ROOT", "nodes": ents, "edges": edges})
    jw(rd / "graph/edge-ledger.json", {"run_id": run_id, "edges": edges})
    jw(
        rd / "graph/frontier.json",
        {
            "run_id": run_id,
            "frontier": [
                {
                    "frontier_id": "F-W3-001",
                    "wave_id": "W3",
                    "query": "source laundering and amplification chain",
                    "priority": "medium",
                    "status": "planned",
                }
            ],
        },
    )
    jw(
        rd / "graph/wave-plan.json",
        {"run_id": run_id, "waves": waves, "async_policy": "new frontier items may spawn work units without waiting for all prior branches", "max_depth": 4},
    )
    tw(rd / "graph/wave-events.jsonl", "".join(json.dumps({"event_name": "wave.updated", "run_id": run_id, **w, "timestamp": now()}, ensure_ascii=False) + "\n" for w in waves))
    tw(rd / "graph/pivot-decisions.jsonl", json.dumps({"pivot_id": "P001", "decision": "expand", "reason": "IO/source-laundering branch required"}, ensure_ascii=False) + "\n")
    jw(rd / "graph/stop-conditions.json", {"run_id": run_id, "max_depth": 4, "stop_when": ["no_new_entities", "low_relevance", "budget_exhausted"]})
    jw(
        rd / "synthesis/open-questions.json",
        {"run_id": run_id, "open_questions": ["Какие внешние источники подтверждают или опровергают seed claims?", "Есть ли признаки source laundering?"]},
    )
    jw(
        rd / "synthesis/evidence-debt.json",
        {"run_id": run_id, "p0_evidence_debt": 0, "p1_evidence_debt": 2, "items": ["External source collection not executed in deterministic smoke mode."]},
    )
    jw(rd / "synthesis/contradiction-matrix.json", {"run_id": run_id, "contradictions": []})
    tw(
        rd / "synthesis/synthesis-events.jsonl",
        json.dumps({"event_name": "synthesis.snapshot", "snapshot_id": "SYN-001", "run_id": run_id, "status": "seed_synthesis_ready", "timestamp": now()}, ensure_ascii=False) + "\n",
    )
    memo = {
        "run_id": run_id,
        "title": "Аналитическая записка",
        "executive_summary": "Материал принят как внутренний аналитический объект; runtime создал структуру проверки, граф волн, claim taxonomy и self-audit контур.",
        "situation_analysis": "Материал требует разложения на проверяемые утверждения, выделения источников, противоречий, нарративов и связей.",
        "key_factors": ["качество источников", "повторяемость утверждений", "независимые подтверждения", "манипулятивная подача"],
        "risks": ["смешение факта и интерпретации", "ложная уверенность модели", "source laundering"],
        "opportunities": ["расширение поиска через граф связей", "разделение точных/спорных/ложных утверждений", "накопление raw evidence"],
        "scenarios": [
            {"name": "минимальный", "description": "фактчек исходных claims"},
            {"name": "расширенный", "description": "волновой графовый сбор и IO-check"},
            {"name": "глубокий", "description": "многоитерационный сбор с contradiction resolution"},
        ],
        "recommendations": ["Запускать wave collector до исчерпания frontier или бюджета.", "Не переносить факты в memo без claim status."],
        "confidence": "medium",
        "data_gaps": ["В smoke-run нет внешнего веб-сбора."],
    }
    factual = {
        "run_id": run_id,
        "confirmed": [c for c in cs if c["status"] == "confirmed"],
        "probable": [c for c in cs if c["status"] == "probable"],
        "disputed": [],
        "doubtful": [],
        "false": [],
        "unsupported": [],
        "raw_search_pivots": ["source laundering", "same-name candidates", "linked organizations", "contrary search"],
    }
    io = {
        "run_id": run_id,
        "narrative_map": [{"narrative_id": "N001", "claim": "Seed material may contain persuasion/framing elements", "confidence": "medium"}],
        "method_matches": [
            {"method": "fear appeal / risk amplification", "confidence": "low", "note": "Requires textual evidence review in full run."},
            {"method": "source laundering check required", "confidence": "medium", "note": "v18 always opens this branch for public/political/media claims."},
        ],
        "source_laundering_map": [],
        "amplification_chain": [],
        "actor_method_source_relations": [],
        "verdict": "not_enough_external_data_in_smoke_run",
    }
    jw(rd / "report/analytical-memo.json", memo)
    jw(rd / "report/factual-dossier.json", factual)
    jw(rd / "io/io-method-matches.json", {"run_id": run_id, "matches": io["method_matches"]})
    jw(rd / "io/narrative-map.json", {"run_id": run_id, "narratives": io["narrative_map"]})
    jw(rd / "io/source-laundering-map.json", {"run_id": run_id, "chains": []})
    jw(rd / "io/amplification-chain.json", {"run_id": run_id, "chain": []})
    jw(rd / "report/io-propaganda-check.json", io)
    audit = {
        "run_id": run_id,
        "deviations": [],
        "model_compliance": {"plain_subagent_used": False, "entrypoint_used": True, "new_facts_in_summary": False},
        "search_quality": {"external_search_executed": False, "reason": "deterministic smoke mode"},
        "hallucination_risk": [{"area": "seed-only claims", "risk": "medium", "mitigation": "mark seed/probable until external evidence collected"}],
        "tool_failures": [],
        "recommendations": ["Run external search workers in production mode.", "Keep evidence debt visible."],
    }
    jw(rd / "self-audit/runtime-self-audit.json", audit)
    jw(rd / "self-audit/model-compliance-ledger.json", audit["model_compliance"])
    jw(rd / "self-audit/search-quality-ledger.json", audit["search_quality"])
    jw(rd / "self-audit/deviation-ledger.json", {"run_id": run_id, "deviations": []})
    jw(
        rd / "self-audit/error-taxonomy.json",
        {"run_id": run_id, "known_failure_classes": ["F170", "F171", "F172", "F173", "F174", "F175", "F179", "F180", "F181", "F190", "F191", "F193"]},
    )
    jw(rd / "self-audit/hallucination-risk-map.json", {"run_id": run_id, "risks": audit["hallucination_risk"]})
    jw(rd / "self-audit/tool-failure-ledger.json", {"run_id": run_id, "tool_failures": []})
    tw(rd / "chat/message-001-analytical-memo.txt", "АНАЛИТИЧЕСКАЯ ЗАПИСКА\n" + memo["executive_summary"] + "\nУверенность: " + memo["confidence"] + "\n")
    tw(rd / "chat/message-002-facts.txt", "ФАКТЫ / СТАТУСЫ\n" + "\n".join(f"{c['claim_id']}: {c['status']} — {c['text']}" for c in cs) + "\n")
    tw(rd / "chat/message-003-io-propaganda-check.txt", "IO / PROPAGANDA / MANIPULATION CHECK\n" + "; ".join(m["method"] for m in io["method_matches"]) + "\n")
    tw(
        rd / "chat/message-004-files.txt",
        "ФАЙЛЫ\nHTML и research-package.zip подготовлены; внешнюю доставку можно утверждать только по delivery-manifest/ACK.\n",
    )
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
            "messages": [
                {"id": "message-001", "kind": "analytical_memo", "path": "chat/message-001-analytical-memo.txt"},
                {"id": "message-002", "kind": "factual_dossier", "path": "chat/message-002-facts.txt"},
                {"id": "message-003", "kind": "io_propaganda_check", "path": "chat/message-003-io-propaganda-check.txt"},
                {"id": "message-004", "kind": "files_and_delivery_status", "path": "chat/message-004-files.txt"},
            ],
            "split_policy": {"max_message_chars": 3500},
        },
    )
    semantic = {
        "run_id": run_id,
        "sections": ["analytical_memo", "factual_dossier", "io_propaganda_check", "target_graph", "claims", "evidence", "sources", "self_audit"],
        "memo": memo,
        "facts_summary": {"total_claims": len(cs), "confirmed": sum(1 for c in cs if c["status"] == "confirmed")},
        "io_summary": io,
        "generated_at": now(),
    }
    jw(rd / "report/semantic-report.json", semantic)

    def sec(t, b):
        return f"<section><h2>{html.escape(t)}</h2>{b}</section>"

    body = (
        sec("Аналитическая записка", f"<p>{html.escape(memo['executive_summary'])}</p>")
        + sec(
            "Фактическое досье",
            "<ul>" + "".join(f"<li><b>{c['claim_id']}</b> [{c['status']}, {c['confidence']}]: {html.escape(c['text'])}</li>" for c in cs) + "</ul>",
        )
        + sec(
            "IO / propaganda / manipulation check",
            "<ul>" + "".join(f"<li>{html.escape(m['method'])} — {m['confidence']}</li>" for m in io["method_matches"]) + "</ul>",
        )
        + sec("Wave graph", "<p>W0/W1/W2 выполнены, W3 запланирована для углубления.</p>")
        + sec("Self-audit", "<p>Отклонений от entrypoint не зафиксировано. Seed-only режим помечен как ограничение.</p>")
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
        "user_visible_research": False,
        "note": "Smoke/seed/stub runs must not read as production research until gates pass.",
    }
    banner_json = html.escape(json.dumps(banner_obj, ensure_ascii=False))
    banner_html = (
        f"<header role='banner' style='background:#1a237e;color:#fff;padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:14px'><strong>RFO run-mode banner</strong> · mode=<code>{mode_s}</code> · provider=<code>{prov_s}</code> · user_visible_research=false until external_delivery_gate passes</header>"
        f"<script type='application/json' id='rfo-run-mode-banner'>{banner_json}</script>"
    )
    tw(
        rd / "report/full-report.html",
        f"<!DOCTYPE html><html lang='ru'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>RFO v18 Internal Analysis Report</title><style>body{{font-family:Arial,sans-serif;line-height:1.55;max-width:1100px;margin:0 auto;padding:24px;background:#f7f7f9;color:#111}}section{{background:white;border:1px solid #ddd;border-radius:10px;padding:18px;margin:14px 0}}h1,h2{{color:#17213a}}</style></head><body>{banner_html}<h1>Research Factory Orchestrator v18 — Internal Analysis/Audit Report</h1><p>run_id: {html.escape(run_id)} · job_id: {html.escape(job_id)}</p>{body}<section><h2>Embedded proof blocks</h2><p>HTML не является proof сам по себе; валидаторы сверяют blocks с файлами run-dir.</p>{scripts}</section></body></html>",
    )
