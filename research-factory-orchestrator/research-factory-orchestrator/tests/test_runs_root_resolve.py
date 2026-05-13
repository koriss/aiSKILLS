"""Tests for ``resolve_default_runs_root`` (bridge CLI default)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL / "scripts"))

from _rfo_path_guard import resolve_default_runs_root  # noqa: E402


class TestResolveDefaultRunsRoot(unittest.TestCase):
    def test_rfo_runs_root_env_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            want = Path(tmp) / "custom" / "runs"
            env = os.environ.copy()
            env["RFO_RUNS_ROOT"] = str(want)
            with mock.patch.dict(os.environ, env, clear=True):
                got = resolve_default_runs_root()
            self.assertEqual(got, want.resolve(strict=False))

    def test_openclaw_workspace_prefers_oc_rfo_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp)
            ws = fake_home / ".openclaw" / "workspace"
            ws.mkdir(parents=True)
            env = os.environ.copy()
            env.pop("RFO_RUNS_ROOT", None)
            with mock.patch.object(Path, "home", return_value=fake_home):
                with mock.patch.dict(os.environ, env, clear=True):
                    got = resolve_default_runs_root()
            self.assertEqual(got, fake_home / ".openclaw" / "workspace" / "rfo-runs")

    def test_portable_fallback_without_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp)
            env = os.environ.copy()
            env.pop("RFO_RUNS_ROOT", None)
            with mock.patch.object(Path, "home", return_value=fake_home):
                with mock.patch.dict(os.environ, env, clear=True):
                    got = resolve_default_runs_root()
            self.assertEqual(got, fake_home / "rfo-runs")


if __name__ == "__main__":
    unittest.main()
