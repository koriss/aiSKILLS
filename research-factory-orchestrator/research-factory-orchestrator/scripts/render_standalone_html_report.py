#!/usr/bin/env python3
from pathlib import Path
import argparse, json, html

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    root = Path(args.run_dir)
    semantic = json.loads((root / "report" / "semantic-report.json").read_text(encoding="utf-8"))
    artifact = json.loads((root / "artifact-manifest.json").read_text(encoding="utf-8"))
    prov = json.loads((root / "provenance-manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "validation-transcript.json").read_text(encoding="utf-8"))
    delivery = json.loads((root / "delivery-manifest.json").read_text(encoding="utf-8"))
    title = html.escape(semantic.get("report_meta", {}).get("topic", "Research report"))

    body = (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<style>body{font-family:system-ui;margin:0;background:#f7f7f5;color:#171717}'
        '.shell{max-width:1100px;margin:auto;padding:16px}.section{background:white;border:1px solid #ddd;border-radius:16px;padding:18px;margin:16px 0}'
        '.table-wrap{overflow-x:auto}.banner{background:#111;color:white;text-align:center;padding:10px;font-weight:700}</style>'
        '</head><body><div class="banner">ТОЛЬКО ДЛЯ СЛУЖЕБНОГО ПОЛЬЗОВАНИЯ · НЕ ДЛЯ ПУБЛИЧНОГО РАСПРОСТРАНЕНИЯ</div>'
        '<main class="shell"><section class="section"><h1>' + title + '</h1><p>Standalone report generated from semantic-report.json.</p></section>'
        '<section class="section"><h2>Structured data</h2><div class="table-wrap"><table><tr><th>Field</th><th>Value</th></tr><tr><td>Status</td><td>Generated</td></tr></table></div></section>'
        '<footer class="section"><strong>Ограничение использования:</strong> материалы «для служебного пользования» не предназначены для обнародования или противоправных целей.</footer></main>'
        '<script type="application/json" id="semantic-report-json">' + json.dumps(semantic, ensure_ascii=False) + '</script>'
        '<script type="application/json" id="artifact-manifest-json">' + json.dumps(artifact, ensure_ascii=False) + '</script>'
        '<script type="application/json" id="provenance-manifest-json">' + json.dumps(prov, ensure_ascii=False) + '</script>'
        '<script type="application/json" id="validation-transcript-json">' + json.dumps(validation, ensure_ascii=False) + '</script>'
        '<script type="application/json" id="delivery-manifest-json">' + json.dumps(delivery, ensure_ascii=False) + '</script>'
        '</body></html>'
    )
    out = root / "report" / "full-report.html"
    out.write_text(body, encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
