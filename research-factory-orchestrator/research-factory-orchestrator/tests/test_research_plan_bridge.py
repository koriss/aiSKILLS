"""Research plan disk contract, early run_dir bootstrap, and query-list fanout."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from runtime.research_bridge_bootstrap import bootstrap_early_run_dir, write_off_mode_research_plan  # noqa: E402
from runtime.research_plan_planner import (  # noqa: E402
    default_safety_caps,
    flatten_plan_queries,
    plan_and_write,
)
from rfo_query_fanout import fanout_relay_search_from_queries  # noqa: E402


def _fake_query(_base: str, q: str, _n: int) -> list[dict]:
    return [{"url": f"https://example.test/{q}", "title": q, "snippet": "x"}]


class TestResearchPlanBridge(unittest.TestCase):
    def test_bootstrap_writes_research_dir_before_relay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rd = Path(td) / "runs" / "smoke_label"
            rd.mkdir(parents=True)
            bootstrap_early_run_dir(rd, run_id="RUN-test", task="probe task")
            self.assertTrue((rd / "research").is_dir())
            self.assertTrue((rd / "graph").is_dir())
            log = rd / "research" / "bridge-phase-log.jsonl"
            self.assertTrue(log.is_file())
            lines = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertTrue(lines)
            row = json.loads(lines[0])
            self.assertEqual(row.get("event_name"), "bridge.run_dir_bootstrapped")

    def test_fanout_from_queries_sequential_merge_stats(self) -> None:
        rows, stats = fanout_relay_search_from_queries(
            _fake_query,
            ["https://relay.example/"],
            ["alpha", "alpha", "beta"],
            2,
        )
        urls = {r.get("url") for r in rows}
        self.assertIn("https://example.test/alpha", urls)
        self.assertIn("https://example.test/beta", urls)
        self.assertEqual(stats.get("fanout_source"), "explicit_query_list")

    def test_plan_and_write_fallback_without_planner_api(self) -> None:
        prev_base = os.environ.pop("RFO_RESEARCH_PLANNER_BASE_URL", None)
        prev_key = os.environ.pop("RFO_RESEARCH_PLANNER_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as td:
                rd = Path(td)
                summary = plan_and_write(rd, "synthetic topic for unittest")
                self.assertTrue(summary.get("used_fallback"))
                p = rd / "research" / "research-plan.json"
                self.assertTrue(p.is_file())
                doc = json.loads(p.read_text(encoding="utf-8"))
                self.assertEqual(doc.get("schema_version"), "research-plan-v1")
                flat = flatten_plan_queries(doc)
                self.assertTrue(flat)
        finally:
            if prev_base is not None:
                os.environ["RFO_RESEARCH_PLANNER_BASE_URL"] = prev_base
            if prev_key is not None:
                os.environ["RFO_RESEARCH_PLANNER_API_KEY"] = prev_key

    def test_off_mode_plan_matches_template_vectors(self) -> None:
        from rfo_query_fanout import build_query_vectors

        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            (rd / "research").mkdir(parents=True)
            task = "compare two APIs"
            vectors = build_query_vectors(task)
            write_off_mode_research_plan(rd, task, queries=vectors, safety=default_safety_caps())
            doc = json.loads((rd / "research" / "research-plan.json").read_text(encoding="utf-8"))
            w0 = (doc.get("waves") or [{}])[0]
            self.assertEqual(w0.get("queries"), vectors)


if __name__ == "__main__":
    unittest.main()
