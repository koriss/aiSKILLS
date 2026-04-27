#!/usr/bin/env python3
from pathlib import Path

FORBIDDEN = [
    "deep-investigation-agent",
    "task-launch-protocol",
    "multi-search-engine"
]

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    targets = [root / "SKILL.md", root / "README.md"] + list((root / "templates").glob("*.md"))
    bad = []
    for t in targets:
        text = t.read_text(encoding="utf-8").lower()
        for f in FORBIDDEN:
            if f in text:
                bad.append((t, f))
    if bad:
        for path, token in bad:
            print(f"Forbidden reference '{token}' in {path}")
        raise SystemExit(1)
    print("No forbidden external skill references found.")

if __name__ == "__main__":
    main()
