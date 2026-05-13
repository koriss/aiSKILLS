"""Unit tests for ``scripts/assert_no_relay_semantics.py`` strict JSON scan."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_assert_mod():
    path = _skill_root() / "scripts" / "assert_no_relay_semantics.py"
    spec = importlib.util.spec_from_file_location("_assert_no_relay_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAssertNoRelaySemantics(unittest.TestCase):
    def test_v2_snapshot_clean_passes(self):
        mod = _load_assert_mod()
        snap = {
            "schema": "rfo-effective-config-v2",
            "relay": None,
            "relay_source": "none_agent_supplied_packet",
            "relay_chain": [],
            "web_search_json_api_base": None,
        }
        hits: list[str] = []
        mod._walk(snap, "effective-config.json", hits)
        self.assertEqual(hits, [])

    def test_relay_chain_non_empty_fails(self):
        mod = _load_assert_mod()
        snap = {
            "relay_chain": ["https://relay.example/search"],
            "relay_source": "none_agent_supplied_packet",
        }
        hits: list[str] = []
        mod._walk(snap, "x.json", hits)
        self.assertTrue(any("relay_chain" in h for h in hits))

    def test_web_search_json_api_base_fails(self):
        mod = _load_assert_mod()
        snap = {"web_search_json_api_base": "http://127.0.0.1:9/"}
        hits: list[str] = []
        mod._walk(snap, "x.json", hits)
        self.assertTrue(hits)

    def test_cli_run_dir_scan_empty_ok(self):
        skill = _skill_root()
        exe = skill / "scripts" / "assert_no_relay_semantics.py"
        with tempfile.TemporaryDirectory() as tmp:
            rd = Path(tmp)
            (rd / "effective-config.json").write_text(
                json.dumps(
                    {
                        "schema": "rfo-effective-config-v2",
                        "relay": None,
                        "relay_source": "none_agent_supplied_packet",
                        "relay_chain": [],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-S", str(exe), "--run-dir", str(rd)],
                cwd=str(skill),
                capture_output=True,
                text=True,
                timeout=15,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
