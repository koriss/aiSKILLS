"""MD-first dossier: Markdown canonical, HTML derived only from that string."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from runtime.report_html import (
    build_full_report_html_from_markdown,
    md_to_html_body,
    rebuild_canonical_md_then_html,
)
from runtime.report_md import FULL_REPORT_MD_REL, build_full_report_md, write_canonical_full_report_md
from runtime.report_inputs import ReportRunInputs


class TestMdFirstPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "html-report-run"
            / "dbg-full-20260508-151447"
        )
        self.assertTrue(self.fixture.is_dir(), f"missing fixture: {self.fixture}")

    def test_rebuild_writes_non_empty_md_and_html(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="rfo-md-first-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        shutil.copytree(self.fixture, tmp, dirs_exist_ok=True)
        ok, msg = rebuild_canonical_md_then_html(tmp, source="test")
        self.assertTrue(ok, msg)
        md_p = tmp / FULL_REPORT_MD_REL
        html_p = tmp / "report/full-report.html"
        self.assertTrue(md_p.is_file(), "full-report.md missing")
        self.assertGreater(md_p.stat().st_size, 64, "md should not be trivially empty")
        self.assertTrue(html_p.is_file(), "full-report.html missing")
        head = html_p.read_text(encoding="utf-8", errors="replace")
        self.assertIn("<!DOCTYPE html>", head[:800])
        self.assertIn("rfo-md-first", head)

    def test_html_from_markdown_includes_proof_section(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="rfo-md-html-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        shutil.copytree(self.fixture, tmp, dirs_exist_ok=True)
        inputs = ReportRunInputs.from_run_dir(tmp)
        md_doc = build_full_report_md(inputs)
        write_canonical_full_report_md(tmp, md_doc, source="test")
        html_doc = build_full_report_html_from_markdown(tmp, md_doc)
        self.assertIn("embedded-proof-blocks", html_doc)
        self.assertRegex(html_doc, r'id="run-json-json"')

    def test_md_to_html_body_produces_html_or_pre(self) -> None:
        frag = md_to_html_body("# Title\n\n|a|b|\n|-|-|\n|1|2|\n")
        self.assertTrue(frag.strip())
        self.assertTrue("<h1" in frag or "<pre" in frag)


if __name__ == "__main__":
    unittest.main()
