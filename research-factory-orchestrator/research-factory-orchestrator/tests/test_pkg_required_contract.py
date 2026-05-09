"""Contract parity and PKG_REQUIRED scaffold coverage."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from runtime.pkg_required_scaffold import ensure_pkg_required_paths, load_package_contract  # noqa: E402
from runtime.schema_synth import schema_core_path  # noqa: E402
from runtime.util import PKG_REQUIRED, load_pkg_required_paths, package_required_artifacts_path  # noqa: E402


class TestPkgRequiredContract(unittest.TestCase):
    def test_pkg_required_matches_contract_paths(self) -> None:
        cont_path = package_required_artifacts_path()
        self.assertTrue(cont_path.is_file(), msg=str(cont_path))
        cont = json.loads(cont_path.read_text(encoding="utf-8"))
        rels = [a["relpath"] for a in cont["artifacts"] if isinstance(a, dict)]
        self.assertEqual(rels, PKG_REQUIRED)
        self.assertEqual(load_pkg_required_paths(), PKG_REQUIRED)

    def test_contract_schema_files_exist(self) -> None:
        cont = load_package_contract()
        for a in cont["artifacts"]:
            self.assertIsInstance(a, dict)
            kind = (a.get("kind") or "json").strip().lower()
            if kind == "json":
                cs = a.get("core_schema") or "pkg-generic-object"
                self.assertTrue(schema_core_path(str(cs)).is_file(), msg=f"missing schema for {cs}")
            elif kind == "jsonl":
                ls = a.get("line_schema") or "pkg-jsonl-event"
                self.assertTrue(schema_core_path(str(ls)).is_file(), msg=f"missing line schema for {ls}")
            elif kind == "text":
                cs = a.get("core_schema")
                self.assertIsInstance(cs, str)
                self.assertTrue(cs.strip())
                self.assertTrue(schema_core_path(str(cs)).is_file(), msg=f"missing text schema for {cs}")
            else:
                self.fail(f"unknown kind {kind!r}")

    def test_ensure_pkg_required_materializes_all_paths(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            ensure_pkg_required_paths(tmp, "RUN-test", "JOB-test", "CMD-test")
            missing = [r for r in PKG_REQUIRED if not (tmp / r).is_file()]
            self.assertEqual(missing, [], msg="missing: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
