"""Regression tests for wiki-style HTML report rendering."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from runtime.report_html import (
    TEMPLATE_PATH,
    build_full_report_html,
    build_source_index,
    fill_template,
)
from runtime.status import VERSION


class TestWikiCitations(unittest.TestCase):
    def test_source_index_and_ref_in_output(self) -> None:
        rd = Path(__file__).resolve().parent.parent / "reports" / "debug-runs" / "20260508T151228Z" / "runs" / "dbg-full-20260508-151447"
        if not (rd / "run.json").is_file():
            self.skipTest("fixture run-dir not present")
        sources = json.loads((rd / "sources.json").read_text(encoding="utf-8"))["sources"]
        idx = build_source_index(sources)
        self.assertGreater(len(idx), 0)
        claims = json.loads((rd / "claims-registry.json").read_text(encoding="utf-8"))["claims"]
        memo = json.loads((rd / "report/analytical-memo.json").read_text(encoding="utf-8"))
        io = json.loads((rd / "report/io-propaganda-check.json").read_text(encoding="utf-8"))
        audit = json.loads((rd / "self-audit/runtime-self-audit.json").read_text(encoding="utf-8"))
        factual = json.loads((rd / "report/factual-dossier.json").read_text(encoding="utf-8"))
        evidence = json.loads((rd / "evidence-cards.json").read_text(encoding="utf-8"))["evidence_cards"]
        graph = json.loads((rd / "graph/target-graph.json").read_text(encoding="utf-8"))
        nodes, edges = graph.get("nodes") or [], graph.get("edges") or []
        waves = (json.loads((rd / "graph/wave-plan.json").read_text(encoding="utf-8")).get("waves") or [])
        run = json.loads((rd / "run.json").read_text(encoding="utf-8"))
        html_out = build_full_report_html(
            rd=rd,
            task=str(run.get("task") or ""),
            run_id=str(run.get("run_id") or "X"),
            job_id=str(run.get("job_id") or "X"),
            cmd_id=str(run.get("command_id") or ""),
            provider=str(run.get("provider") or ""),
            memo=memo,
            claims=claims,
            sources=sources,
            evidence=evidence,
            waves=waves,
            nodes=nodes if isinstance(nodes, list) else [],
            edges=edges if isinstance(edges, list) else [],
            io=io,
            audit=audit,
            disclaimer="test",
            user_visible_research=True,
            factual=factual,
            generated_at="2026-01-01T00:00:00Z",
            version=VERSION,
        )
        self.assertIn("#ref-1", html_out)
        self.assertIn("ref-marker", html_out)
        self.assertNotIn("{{", html_out)

    def test_fill_template_no_raw_placeholders(self) -> None:
        tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
        mapping = {m: "<p>x</p>" for m in re.findall(r"\{\{([A-Z0-9_]+)\}\}", tpl)}
        filled = fill_template(tpl, mapping)
        self.assertNotRegex(filled, r"\{\{[A-Z0-9_]+\}\}")


if __name__ == "__main__":
    unittest.main()
