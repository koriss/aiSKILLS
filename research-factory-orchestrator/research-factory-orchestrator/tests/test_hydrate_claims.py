"""Claims hydration + packaging stub policy (relay/worker integration surface)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.render import hydrate_claims_if_needed
from runtime.util import jw, jr
from runtime.worker_impl import _build_package_allow_stub


class TestHydrateClaims(unittest.TestCase):
    def test_hydrates_when_sources_exist_and_claims_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            rd = Path(tmp) / "run"
            rd.mkdir(parents=True, exist_ok=True)
            jw(rd / "run.json", {"run_id": "RUN-TEST", "job_id": "JOB", "command_id": "CMD"})
            jw(
                rd / "collection-result.json",
                {
                    "seed_only": False,
                    "external_source_packet_loaded": True,
                    "external_web_search_executed": False,
                },
            )
            jw(
                rd / "sources.json",
                {
                    "schema_version": "v19.0",
                    "sources": [
                        {
                            "source_id": "SRC-RELAY-001",
                            "title": "Example",
                            "url": "https://example.com/page",
                            "source_role": "background",
                            "content_snippet": "",
                            "content_fetch_error": "timeout",
                        }
                    ],
                },
            )
            jw(rd / "claims-registry.json", {"schema_version": "v19.0", "claims": []})

            ok = hydrate_claims_if_needed(rd, task="test task", run_id="RUN-TEST")
            self.assertTrue(ok)
            reg = jr(rd / "claims-registry.json", {})
            claims = reg.get("claims") or []
            self.assertEqual(len(claims), 1)
            self.assertEqual((claims[0].get("meta") or {}).get("origin"), "hydrate_from_sources")


class TestBuildPackageStub(unittest.TestCase):
    def test_dossier_with_packet_requires_full_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rd = Path(tmp) / "run"
            rd.mkdir(parents=True, exist_ok=True)
            jw(rd / "run-profile.json", {"schema_version": "v19.0", "profile": "dossier"})
            jw(
                rd / "collection-result.json",
                {"seed_only": False, "external_source_packet_loaded": True},
            )
            self.assertFalse(_build_package_allow_stub(rd))

    def test_seed_only_allows_stub_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            rd = Path(tmp) / "run"
            rd.mkdir(parents=True, exist_ok=True)
            jw(rd / "run-profile.json", {"schema_version": "v19.0", "profile": "dossier"})
            jw(rd / "collection-result.json", {"seed_only": True})
            self.assertTrue(_build_package_allow_stub(rd))


if __name__ == "__main__":
    unittest.main()
