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
