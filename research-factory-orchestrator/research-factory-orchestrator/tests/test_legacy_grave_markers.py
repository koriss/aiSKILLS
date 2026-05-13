"""Legacy operator scripts must fatal without starting research (exit 2)."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


_SKILL_ROOT = Path(__file__).resolve().parents[1]


class TestLegacyGraveMarkers(unittest.TestCase):
    def _run_script(self, rel: str) -> tuple[int, str]:
        script = _SKILL_ROOT / rel
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(_SKILL_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode, (proc.stderr or "") + (proc.stdout or "")

    def test_run_rfo_full_research_exits_2_with_hint(self) -> None:
        code, err = self._run_script("scripts/run_rfo_full_research.py")
        self.assertEqual(code, 2)
        self.assertIn("rfo_execute.py", err)

    def test_run_research_factory_exits_2_with_hint(self) -> None:
        code, err = self._run_script("scripts/run_research_factory.py")
        self.assertEqual(code, 2)
        self.assertIn("rfo_execute.py", err)


if __name__ == "__main__":
    unittest.main()
