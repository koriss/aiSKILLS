"""Regression: relay/collector non-schema source keys → V1-clean sources bundles."""
from __future__ import annotations

import json
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "validators" / "core"))

from runtime.collector import _update_sources_with_collection  # noqa: E402
from v19_stdlib_schema_walk import validate_instance  # noqa: E402


def _sources_bundle_schema() -> dict:
    p = ROOT / "schemas" / "core" / "sources.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _assert_bundle_schema(obj: dict, *, label: str) -> None:
    schema = _sources_bundle_schema()
    errs = list(
        validate_instance(obj, schema, root=schema, path="$", issue_code="TEST-SOURCES", strict_additional=True),
    )
    if errs:
        raise AssertionError(f"{label}: {errs}")


def _load_patch_bridge() -> object:
    spec = importlib.util.spec_from_file_location(
        "run_rfo_with_web_search",
        ROOT / "scripts" / "run_rfo_with_web_search.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRelaySourcesSchemaNormalization(unittest.TestCase):
    def test_patch_sources_json_strips_relay_noise(self) -> None:
        mod = _load_patch_bridge()
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run-relay-schema"
            run.mkdir(parents=True)
            dirty = {
                "source_id": "relay-1",
                "title": "Example page",
                "canonical_origin_id": "https://example.com/p",
                "url": "https://example.com/p",
                "source_role": "background",
                "access_level": "primary_access",
                "interest_alignment": "neutral",
                "verification_mode": "snippet_only",
                "independence": "medium",
                "citation_eligible": False,
                "corroboration_type": "authoritative",
                "fetch_method": "relay",
                "content_fetch_error": "none",
                "citation_scope": "snippet_only",
            }
            mod.patch_sources_json(run, [dirty])
            root = json.loads((run / "sources.json").read_text(encoding="utf-8"))
            _assert_bundle_schema(root, label="patch_sources_json root")
            src0 = root["sources"][0]
            self.assertNotIn("fetch_method", src0)
            self.assertNotIn("citation_scope", src0)
            self.assertEqual(src0.get("source_role"), "unknown")
            self.assertEqual(src0.get("interest_alignment"), "unknown")
            self.assertEqual(src0.get("corroboration_type"), "independent")

    def test_collector_merge_normalizes_sources(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run-collector"
            run.mkdir(parents=True)
            dirty = {
                "source_id": "pkt-1",
                "title": "Packet row",
                "canonical_origin_id": "https://example.org/q",
                "url": "https://example.org/q",
                "source_role": "background",
                "access_level": "primary_access",
                "interest_alignment": "neutral",
                "verification_mode": "raw_document",
                "independence": "high",
                "citation_eligible": True,
                "corroboration_type": "corroborated",
                "fetch_method": "source_packet",
                "citation_scope": "raw_document",
            }
            summary = {
                "run_id": run.name,
                "seed_only": False,
                "synthetic_count": 0,
            }
            _update_sources_with_collection(run, summary, [dirty])
            root = json.loads((run / "sources.json").read_text(encoding="utf-8"))
            _assert_bundle_schema(root, label="collector root")
            self.assertTrue((run / "sources" / "sources.json").is_file())
            sub = json.loads((run / "sources" / "sources.json").read_text(encoding="utf-8"))
            self.assertEqual(sub.get("run_id"), run.name)
            self.assertNotIn("fetch_method", sub["sources"][0])

    def test_make_claims_reads_content_snippet(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "run_rfo_full_research",
            ROOT / "scripts" / "run_rfo_full_research.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        src = {
            "source_id": "SRC-SNIP-1",
            "title": "T",
            "canonical_origin_id": "https://a.example/x",
            "url": "https://a.example/x",
            "source_role": "unknown",
            "access_level": "primary_access",
            "interest_alignment": "unknown",
            "verification_mode": "raw_document",
            "independence": "medium",
            "citation_eligible": True,
            "corroboration_type": "independent",
            "content_snippet": "x" * 200,
        }
        claims, evidence = mod.make_claims([src])
        self.assertEqual(len(claims), 1)
        self.assertEqual(len(evidence), 1)
        self.assertTrue(claims[0]["claim_text"].startswith("x"))


if __name__ == "__main__":
    unittest.main()
