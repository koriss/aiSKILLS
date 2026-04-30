#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REQUIRED = [
    "MASTER-PROMPT.md", "runtime-contract.json", "session-state.md", "runtime-state.json",
    "artifact-manifest.json", "tool-registry.json", "final-package-manifest.json"
]

def check_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    if "<html" not in text or "</html>" not in text:
        raise ValueError(f"{path} is not valid basic HTML")

def main() -> None:
    p = argparse.ArgumentParser(description="Validate generated runtime artifacts.")
    p.add_argument("--project-dir", required=True)
    args = p.parse_args()
    root = Path(args.project_dir)
    for rel in REQUIRED:
        f = root / rel
        if not f.exists() or f.stat().st_size == 0:
            raise SystemExit(f"Missing or empty required artifact: {rel}")
    for json_file in root.rglob("*.json"):
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"Invalid JSON {json_file}: {exc}")
    for html_file in root.rglob("*.html"):
        if html_file.stat().st_size > 0:
            check_html(html_file)
    manifest = json.loads((root / "artifact-manifest.json").read_text(encoding="utf-8"))
    for art in manifest.get("artifacts", []):
        pth = root / art.get("path", "")
        if not pth.exists():
            raise SystemExit(f"Manifest points to missing file: {art.get('path')}")
    print("Artifacts valid.")

if __name__ == "__main__":
    main()
