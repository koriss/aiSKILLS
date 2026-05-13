"""Contract tests for ``scripts/rfo_execute.py`` source-packet canonical path."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


class TestRfoExecuteSourcePacketContract(unittest.TestCase):
    def test_legacy_task_flag_exit_2(self):
        skill = _skill_root()
        exe = skill / "scripts" / "rfo_execute.py"
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(exe),
                    "--runs-root",
                    str(runs),
                    "--task",
                    "forbidden",
                ],
                cwd=str(skill),
                env={**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1", "RFO_RUN_EXECUTION_MODE": "test_fixture"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("RFO_CONTRACT_CHANGED_SOURCE_PACKET_REQUIRED", proc.stderr)

    def test_missing_default_packet_exit_2(self):
        skill = _skill_root()
        exe = skill / "scripts" / "rfo_execute.py"
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [sys.executable, "-S", str(exe), "--runs-root", str(runs)],
                cwd=str(skill),
                env={**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1", "RFO_RUN_EXECUTION_MODE": "test_fixture"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("RFO_INPUT_SOURCE_PACKET_MISSING", proc.stderr)

    def test_stale_packet_exit_2_without_allow(self):
        skill = _skill_root()
        exe = skill / "scripts" / "rfo_execute.py"
        fix = skill / "tests" / "fixtures" / "source_packets" / "stale_packet.json"
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(exe),
                    "--runs-root",
                    str(runs),
                    "--source-packet",
                    str(fix),
                ],
                cwd=str(skill),
                env={**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1", "RFO_RUN_EXECUTION_MODE": "test_fixture"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("RFO_INPUT_SOURCE_PACKET_STALE", proc.stderr)

    def test_validate_fixture_ok(self):
        skill = _skill_root()
        val = skill / "scripts" / "rfo_validate_source_packet.py"
        fix = skill / "tests" / "fixtures" / "source_packets" / "minimal_ok.json"
        proc = subprocess.run(
            [sys.executable, "-S", str(val), "--source-packet", str(fix)],
            cwd=str(skill),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertTrue(doc.get("ok"))

    def test_stderr_topic_sha_before_run_skipped_if_missing(self):
        """If packet missing, stderr should not claim a sha (sanity on ordering)."""
        skill = _skill_root()
        exe = skill / "scripts" / "rfo_execute.py"
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [sys.executable, "-S", str(exe), "--runs-root", str(runs)],
                cwd=str(skill),
                env={**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1", "RFO_RUN_EXECUTION_MODE": "test_fixture"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        err = proc.stderr or ""
        self.assertNotIn("source_packet_sha256=", err)

    def test_all_fixture_packets_validate(self):
        """Loop every JSON under tests/fixtures/source_packets through the validator."""
        skill = _skill_root()
        val = skill / "scripts" / "rfo_validate_source_packet.py"
        fix_dir = skill / "tests" / "fixtures" / "source_packets"
        paths = sorted(fix_dir.glob("*.json"))
        self.assertTrue(paths, "expected at least one fixture packet")
        for fix in paths:
            with self.subTest(packet=fix.name):
                proc = subprocess.run(
                    [sys.executable, "-S", str(val), "--source-packet", str(fix)],
                    cwd=str(skill),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
                doc = json.loads(proc.stdout)
                self.assertTrue(doc.get("ok"), doc)

    def test_blocked_fixture_validate_ok_execute_refuses(self):
        skill = _skill_root()
        val = skill / "scripts" / "rfo_validate_source_packet.py"
        exe = skill / "scripts" / "rfo_execute.py"
        fix = skill / "tests" / "fixtures" / "source_packets" / "blocked_packet.json"
        proc_v = subprocess.run(
            [sys.executable, "-S", str(val), "--source-packet", str(fix)],
            cwd=str(skill),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(proc_v.returncode, 0, proc_v.stderr + proc_v.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc_e = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(exe),
                    "--runs-root",
                    str(runs),
                    "--source-packet",
                    str(fix),
                    "--allow-stale-packet",
                ],
                cwd=str(skill),
                env={**os.environ, "RFO_ALLOW_TMP_RUNS_ROOT": "1", "RFO_RUN_EXECUTION_MODE": "test_fixture"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc_e.returncode, 2, proc_e.stderr)
        self.assertIn("blocked=true", proc_e.stderr)

    def test_template_mode_accepts_placeholders(self):
        skill = _skill_root()
        val = skill / "scripts" / "rfo_validate_source_packet.py"
        tpl = skill / "templates" / "source-packet.bootstrap.example.json"
        proc = subprocess.run(
            [sys.executable, "-S", str(val), "--source-packet", str(tpl), "--template-mode"],
            cwd=str(skill),
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertTrue(doc.get("ok"))
        self.assertIn("template_placeholder_ok", doc.get("notes") or [])

    def test_forbidden_rfo_run_profile_exit_2(self):
        skill = _skill_root()
        exe = skill / "scripts" / "rfo_execute.py"
        fix = skill / "tests" / "fixtures" / "source_packets" / "minimal_ok.json"
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(exe),
                    "--runs-root",
                    str(runs),
                    "--source-packet",
                    str(fix),
                    "--allow-stale-packet",
                ],
                cwd=str(skill),
                env={
                    **os.environ,
                    "RFO_ALLOW_TMP_RUNS_ROOT": "1",
                    "RFO_RUN_EXECUTION_MODE": "test_fixture",
                    "RFO_RUN_PROFILE": "dossier",
                },
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("forbidden_env=RFO_RUN_PROFILE", proc.stderr)

    def test_import_run_rfo_with_web_search_no_top_level_exit(self):
        """Importing the bridge module must not invoke ``sys.exit`` (only ``__main__`` may exit)."""
        import importlib.util

        skill = _skill_root()
        path = skill / "scripts" / "run_rfo_with_web_search.py"
        spec = importlib.util.spec_from_file_location("_rfo_bridge_import_probe", path)
        self.assertIsNotNone(spec and spec.loader)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.assertTrue(callable(getattr(mod, "main", None)))

    def test_validate_docs_archival_script_passes(self):
        skill = _skill_root()
        script = skill / "scripts" / "validate_docs_archival_markers.py"
        proc = subprocess.run(
            [sys.executable, "-S", str(script)],
            cwd=str(skill),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
