#!/usr/bin/env python3
from pathlib import Path
import argparse, json

def score_archetype(task, arch):
    text = task.lower()
    score = 0
    for term in arch.get("best_for", []):
        if term.lower() in text:
            score += 3
    for term in [arch.get("id",""), arch.get("name","")]:
        if term and term.lower().replace("_", " ") in text:
            score += 2
    return score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--registry", required=True)
    args = ap.parse_args()
    data = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    scored = [(score_archetype(args.task, a), a) for a in data.get("archetypes", [])]
    scored.sort(key=lambda x: (-x[0], x[1].get("id","")))
    best_score, best = scored[0]
    if best_score <= 0:
        best = next(a for a in data["archetypes"] if a["id"] == "compose_from_components")
    print(json.dumps({"selected_archetype": best, "score": best_score}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
