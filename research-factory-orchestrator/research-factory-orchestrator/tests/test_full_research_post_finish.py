"""Citation grounding + feature matrix sync for standalone relay helpers."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from runtime.standalone_relay_driver import (  # noqa: E402
    feature_matrix_standalone,
    post_finish_standalone,
)
from runtime.util import jw  # noqa: E402


class TestFullResearchPostFinish(unittest.TestCase):
    def test_post_finish_writes_citation_and_validator_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            rd = Path(td)
            (rd / "graph").mkdir(parents=True, exist_ok=True)
            jw(
                rd / "collection-result.json",
                {
                    "schema_version": "v19.0",
                    "run_id": "RUN-test",
                    "job_id": "JOB-test",
                    "profile": "search-primary",
                    "backend": "test",
                    "web_search_attempted": True,
                    "web_search_succeeded": True,
                    "external_web_search_executed": True,
                    "external_source_count": 1,
                    "seed_only": False,
                },
            )
            jw(
                rd / "claims-registry.json",
                {
                    "schema_version": "v19.0",
                    "claims": [
                        {
                            "claim_id": "C-1",
                            "claim_text": "Example claim with body text long enough.",
                            "claim_type": "source_derived",
                            "status": "reported_claim",
                            "confidence": "high",
                            "evidence_card_ids": ["EV-1"],
                            "support_set": [
                                {
                                    "source_id": "SRC-1",
                                    "evidence_card_id": "EV-1",
                                    "role_for_claim": "primary_support",
                                },
                                {
                                    "source_id": "SRC-2",
                                    "evidence_card_id": "EV-2",
                                    "role_for_claim": "corroboration",
                                },
                            ],
                        },
                    ],
                },
            )
            jw(rd / "graph/wave-plan.json", {"run_id": "RUN-test", "waves": [{"wave_id": "W0", "status": "completed", "purpose": "test"}]})
            jw(
                rd / "feature-truth-matrix.json",
                feature_matrix_standalone("RUN-test", {"web_search_succeeded": True, "external_web_search_executed": True}),
            )
            entry = {"run_id": "RUN-test", "job_id": "JOB-test", "command_id": "CMD-test"}
            post_finish_standalone(rd, entry, "search-primary")
            cg_path = rd / "citation-grounding-result.json"
            self.assertTrue(cg_path.is_file(), msg="citation-grounding-result.json missing")
            cg = json.loads(cg_path.read_text(encoding="utf-8"))
            self.assertIn("passed", cg)
            self.assertIn("relevance_aware_factuality_score", cg)
            ftm = json.loads((rd / "feature-truth-matrix.json").read_text(encoding="utf-8"))
            self.assertIn("citation_grounding_summary", ftm)
            gate = json.loads((rd / "final-answer-gate.json").read_text(encoding="utf-8"))
            self.assertIn("passed", gate)
            self.assertIn("checks", gate)
            chk = gate["checks"]
            self.assertTrue(chk.get("wave_plan_materialized"))
            self.assertTrue(chk.get("citation_grounding_passed"))
            self.assertEqual(chk.get("driver"), "run_rfo_full_research")
            self.assertTrue(gate.get("passed"), msg="validator_result_present: gate must pass when wave + citation OK")


if __name__ == "__main__":
    unittest.main()
