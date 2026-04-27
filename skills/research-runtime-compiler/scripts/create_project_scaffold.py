#!/usr/bin/env python3
import argparse
from pathlib import Path

ROOT_FILES = [
    "MASTER-PROMPT.md", "runtime-contract.json", "session-state.md", "runtime-state.json",
    "queue.json", "artifact-manifest.json", "tool-registry.json", "final-package-manifest.json",
    "final-summary.md", "logs/runtime.log", "logs/search.log", "logs/validation.log",
    "logs/watchdog.md", "logs/trace.jsonl", "logs/activity-history.html",
    "items/example-item/stage-status.json", "items/example-item/context-snapshot.md",
    "items/example-item/sources.json", "items/example-item/source-index.json",
    "items/example-item/evidence-map.json", "items/example-item/evidence-notes.json",
    "items/example-item/claims-registry.json", "items/example-item/draft.html",
    "items/example-item/fact-check.html", "items/example-item/citation-locator.json",
    "items/example-item/citation-locator.html", "items/example-item/error-audit.json",
    "items/example-item/evaluation-score.json", "items/example-item/final.html",
    "items/example-item/logs.md",
]

def put(path: Path, content: str, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force and path.name in {"final.html", "final-summary.md"}:
        return
    if not path.exists() or force:
        path.write_text(content, encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser(description="Create runtime scaffold (idempotent).")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    base = Path(args.project_dir)
    for rel in ROOT_FILES:
        target = base / rel
        if target.suffix == ".json":
            put(target, "{}\n", args.force)
        elif target.suffix == ".html":
            put(target, "<html><body><h1>placeholder</h1></body></html>\n", args.force)
        else:
            put(target, "# placeholder\n", args.force)
    print(f"Scaffold ready: {base}")

if __name__ == "__main__":
    main()
