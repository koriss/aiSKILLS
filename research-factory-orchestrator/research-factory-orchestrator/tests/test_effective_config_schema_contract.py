"""Contract: effective-config snapshot matches contracts/rfo-effective-config-v1.schema.json."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from runtime.config_resolution import build_effective_config_snapshot


def _load_schema_required(root: Path) -> tuple[dict, list[str]]:
    p = root / "contracts" / "rfo-effective-config-v1.schema.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    req = list(data.get("required") or [])
    return data, req


class TestEffectiveConfigSchemaContract(unittest.TestCase):
    def test_snapshot_has_all_required_keys(self) -> None:
        root = Path(__file__).resolve().parents[1]
        _, required = _load_schema_required(root)
        snap = build_effective_config_snapshot(
            skill_root=root,
            argv=["--runs-root", "/tmp/rfo-runs-test"],
            env={
                "RFO_WEB_SEARCH_JSON_API_BASE": "https://relay.example/json",
            },
            cli_relay_base="",
            profile="dossier",
            entrypoint="test",
        )
        for k in required:
            self.assertIn(k, snap, msg=f"missing required key {k!r} in snapshot")

    def test_canonical_missing_argv_runs_root_blocked(self) -> None:
        root = Path(__file__).resolve().parents[1]
        snap = build_effective_config_snapshot(
            skill_root=root,
            argv=["--task", "x"],
            env={"RFO_WEB_SEARCH_JSON_API_BASE": "https://relay.example/json"},
            cli_relay_base="",
            profile="dossier",
            entrypoint="test",
        )
        self.assertIn("missing_required_argv_runs_root", snap.get("errors") or [])
        self.assertEqual(snap.get("run_execution_mode"), "blocked_external_dependency")
        self.assertEqual(snap.get("blocked_dependency"), "runs_root_argv")
        self.assertFalse(snap.get("production_research"))

    def test_fixture_mode_marks_non_production(self) -> None:
        root = Path(__file__).resolve().parents[1]
        snap = build_effective_config_snapshot(
            skill_root=root,
            argv=["--runs-root", "/tmp/rfo-runs-test"],
            env={
                "RFO_RUN_EXECUTION_MODE": "test_fixture",
                "RFO_WEB_SEARCH_JSON_API_BASE": "https://relay.example/json",
                "RFO_ALLOW_TMP_RUNS_ROOT": "1",
            },
            cli_relay_base="",
            profile="dossier",
            entrypoint="test",
        )
        self.assertTrue(snap.get("fixture_mode"))
        self.assertEqual(snap.get("run_execution_mode"), "test_fixture")
        self.assertFalse(snap.get("production_research"))
        self.assertEqual(snap.get("search_mode"), "fixture_relay")
        root = Path(__file__).resolve().parents[1]
        schema_doc, _ = _load_schema_required(root)
        const = schema_doc.get("properties", {}).get("schema", {}).get("const")
        self.assertEqual(const, "rfo-effective-config-v1")


if __name__ == "__main__":
    unittest.main()
