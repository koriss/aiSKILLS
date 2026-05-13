#!/usr/bin/env python3
"""Unified CLI for RFO HTML renders (subcommands)."""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.report_html import rebuild_canonical_md_then_html, write_canonical_full_report_html  # noqa: E402
from runtime.report_inputs import minimal_report_sources_ready  # noqa: E402

RENDERER_VERSION = "19.4.8-rfo-render-cli-md-first"


def cmd_canonical(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    ok, note = minimal_report_sources_ready(run_dir)
    if not ok:
        sys.stderr.write("cannot render dossier; " + note + "\n")
        return 2
    ok2, note2 = rebuild_canonical_md_then_html(run_dir, source="rfo_render.canonical")
    if not ok2:
        sys.stderr.write("render failed: " + note2 + "\n")
        return 2
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    run_id = str(run.get("run_id") or "UNKNOWN")
    print(
        json.dumps(
            {
                "rendered": True,
                "run_id": run_id,
                "markdown_path": "report/full-report.md",
                "html_path": "report/full-report.html",
                "renderer_version": RENDERER_VERSION,
                "note": note2,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_semantic_shell(args: argparse.Namespace) -> int:
    root = Path(args.run_dir).resolve()
    semantic = json.loads((root / "report" / "semantic-report.json").read_text(encoding="utf-8"))
    artifact = json.loads((root / "artifact-manifest.json").read_text(encoding="utf-8"))
    prov = json.loads((root / "provenance-manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "validation-transcript.json").read_text(encoding="utf-8"))
    delivery = json.loads((root / "delivery-manifest.json").read_text(encoding="utf-8"))
    title = html.escape(semantic.get("report_meta", {}).get("topic", "Research report"))

    body = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<style>body{font-family:system-ui;margin:0;background:#f7f7f5;color:#171717}"
        ".shell{max-width:1100px;margin:auto;padding:16px}.section{background:white;border:1px solid #ddd;border-radius:16px;padding:18px;margin:16px 0}"
        ".table-wrap{overflow-x:auto}.banner{background:#111;color:white;text-align:center;padding:10px;font-weight:700}</style>"
        "</head><body><div class='banner'>ТОЛЬКО ДЛЯ СЛУЖЕБНОГО ПОЛЬЗОВАНИЯ · НЕ ДЛЯ ПУБЛИЧНОГО РАСПРОСТРАНЕНИЯ</div>"
        "<main class='shell'><section class='section'><h1>"
        + title
        + "</h1><p>Standalone report generated from semantic-report.json.</p></section>"
        "<section class='section'><h2>Structured data</h2><div class='table-wrap'><table>"
        "<tr><th>Field</th><th>Value</th></tr><tr><td>Status</td><td>Generated</td></tr></table></div></section>"
        "<footer class='section'><strong>Ограничение использования:</strong> "
        "материалы «для служебного пользования» не предназначены для обнародования или противоправных целей."
        "</footer></main>"
        "<script type='application/json' id='semantic-report-json'>"
        + json.dumps(semantic, ensure_ascii=False)
        + "</script>"
        "<script type='application/json' id='artifact-manifest-json'>"
        + json.dumps(artifact, ensure_ascii=False)
        + "</script>"
        "<script type='application/json' id='provenance-manifest-json'>"
        + json.dumps(prov, ensure_ascii=False)
        + "</script>"
        "<script type='application/json' id='validation-transcript-json'>"
        + json.dumps(validation, ensure_ascii=False)
        + "</script>"
        "<script type='application/json' id='delivery-manifest-json'>"
        + json.dumps(delivery, ensure_ascii=False)
        + "</script>"
        "</body></html>"
    )
    outp = write_canonical_full_report_html(root, body, source="rfo_render.semantic_shell")
    print(str(outp))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="RFO HTML render helpers (canonical template vs semantic shell).")
    sub = ap.add_subparsers(dest="command", required=True)

    pc = sub.add_parser(
        "canonical",
        help="Template + wiki-citations pipeline (same contract as runtime render_all).",
    )
    pc.add_argument("--run-dir", required=True)
    pc.set_defaults(func=cmd_canonical)

    ps = sub.add_parser(
        "semantic-shell",
        help="Minimal single-file HTML from semantic-report.json + manifests (legacy scaffold).",
    )
    ps.add_argument("--run-dir", required=True)
    ps.set_defaults(func=cmd_semantic_shell)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    fn = getattr(args, "func", None)
    if fn is None:
        return 2
    return int(fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
