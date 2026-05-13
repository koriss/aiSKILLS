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

    def test_schema_const(self) -> None:
        root = Path(__file__).resolve().parents[1]
        schema_doc, _ = _load_schema_required(root)
        const = schema_doc.get("properties", {}).get("schema", {}).get("const")
        self.assertEqual(const, "rfo-effective-config-v1")


if __name__ == "__main__":
    unittest.main()
