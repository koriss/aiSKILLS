#!/usr/bin/env python3
"""
Сборка HTML из final-report.json + templates/report.html
Запуск: python3 assemble_report.py path/to/final-report.json [out.html]
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def li_items(lines: list[str]) -> str:
    return "".join(f"<li>{esc(x)}</li>" for x in lines)


def table_claims(rows: list[dict]) -> str:
    out = []
    for r in rows:
        out.append(
            "<tr><td>{c}</td><td>{s}</td><td>{e}</td></tr>".format(
                c=esc(r.get("claim", "")),
                s=esc(r.get("status", "")),
                e=esc("; ".join(r.get("evidence") or [])),
            )
        )
    return "\n".join(out) if out else "<tr><td colspan='3'>—</td></tr>"


def table_timeline(items: list[dict]) -> str:
    rows = []
    for it in items:
        rows.append(
            "<tr><td>{d}</td><td>{e}</td></tr>".format(
                d=esc(it.get("date", "")),
                e=esc(it.get("event", "")),
            )
        )
    return "\n".join(rows) if rows else "<tr><td colspan='2'>—</td></tr>"


def table_actors(items: list[dict]) -> str:
    rows = []
    for it in items:
        rows.append(
            "<tr><td>{n}</td><td>{i}</td><td>{c}</td><td>{x}</td></tr>".format(
                n=esc(it.get("name", "")),
                i=esc(", ".join(it.get("interests") or [])),
                c=esc(", ".join(it.get("capabilities") or [])),
                x=esc(", ".join(it.get("constraints") or [])),
            )
        )
    return "\n".join(rows) if rows else "<tr><td colspan='4'>—</td></tr>"


def hypotheses_html(hyps: list[dict]) -> str:
    blocks = []
    for h in hyps:
        hid = esc(h.get("id", ""))
        blocks.append(f"<h3>Гипотеза {hid}</h3><p>{esc(h.get('summary',''))}</p>")
        blocks.append("<p><strong>Поддержка:</strong> " + esc("; ".join(h.get("support") or [])) + "</p>")
        blocks.append(
            "<p><strong>Противоречия:</strong> " + esc("; ".join(h.get("contradictions") or [])) + "</p>"
        )
        blocks.append("<p><strong>Уверенность:</strong> " + esc(h.get("confidence", "")) + "</p>")
    return "\n".join(blocks) if blocks else "<p>—</p>"


def build_from_final_report(data: dict) -> str:
    inv = data["investigation_report"]
    tpl = (ROOT / "templates" / "report.html").read_text(encoding="utf-8")
    title = inv["main_answer"][:120].replace("\n", " ")
    exec_lines = inv.get("executive_summary") or []
    mapping = {
        "[SLUG]": esc(data.get("slug", "report")),
        "[DATE]": esc(data.get("date", "")),
        "[TITLE]": esc(title),
        "[MODE]": esc(data.get("mode", "")),
        "[REQUEST_ID]": esc(data.get("request_id", "")),
        "[EXEC_SUMMARY_PARAGRAPHS]": esc("\n\n".join(exec_lines)),
        "[MAIN_QUESTION]": esc(inv.get("main_answer", "")),
        "[SUBQUESTIONS_LIST]": "<li>(добавьте подвопросы вручную или расширьте JSON)</li>",
        "[DATA_PLAN_STEPS]": "<li>Сбор первичных источников</li><li>Поиск противоречий</li><li>Синтез</li>",
        "[FACTS_LIST]": li_items(inv.get("established_facts") or []),
        "[CLAIMS_TABLE_ROWS]": table_claims(inv.get("key_claims") or []),
        "[EVIDENCE_MAP_NARRATIVE]": esc("См. таблицу ниже."),
        "[EVIDENCE_MAP_ROWS]": "<tr><td colspan='4'>—</td></tr>",
        "[TIMELINE_ROWS]": table_timeline(inv.get("timeline") or []),
        "[ACTORS_ROWS]": table_actors(inv.get("actors") or []),
        "[CAUSAL_CHAIN]": esc("; ".join(inv.get("non_obvious_links") or [])),
        "[CONTRADICTIONS_LIST]": li_items(
            [c for h in inv.get("hypotheses") or [] for c in (h.get("contradictions") or [])][:20]
        ),
        "[HYPOTHESES_BLOCKS]": hypotheses_html(inv.get("hypotheses") or []),
        "[CONFIDENCE_LEVEL]": esc(inv.get("confidence", {}).get("overall", "")),
        "[CONFIDENCE_RATIONALE]": esc(inv.get("confidence", {}).get("rationale", "")),
        "[UNKNOWNS_LIST]": li_items(inv.get("unknowns") or []),
        "[SUBAGENT_CRITIC_LINES]": "<li>—</li>",
        "[SOURCES_PRIMARY]": li_items(inv.get("sources", {}).get("primary") or []),
        "[SOURCES_SECONDARY]": li_items(inv.get("sources", {}).get("secondary") or []),
        "[SOURCES_CONTEXTUAL]": li_items(inv.get("sources", {}).get("contextual") or []),
        "[STOP_REASON]": esc("complete"),
    }
    out = tpl
    for k, v in mapping.items():
        out = out.replace(k, v)
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 assemble_report.py final-report.json [out.html]")
        sys.exit(2)
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    html_out = build_from_final_report(data)
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        slug = data.get("slug", "report")
        date = data.get("date", "undated")
        out_path = Path(f"{slug}-{date}.html")
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path} ({len(html_out)} bytes)")


if __name__ == "__main__":
    main()
