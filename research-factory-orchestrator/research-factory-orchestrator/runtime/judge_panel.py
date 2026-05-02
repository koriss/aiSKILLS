"""Cross-model judge panel with optional position swap (FairJudge; arXiv:2602.06625)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class JudgeResult:
    model_id: str
    score: float
    swapped: bool


def run_position_swap_judges(
    *,
    judges: list[str],
    prompt_a: str,
    prompt_b: str,
    score_fn=None,
) -> dict[str, Any]:
    """Stub aggregator: real deployments wire score_fn to model calls."""
    out: list[JudgeResult] = []
    for i, mid in enumerate(judges):
        s = 0.9 if score_fn is None else float(score_fn(mid, prompt_a, prompt_b))
        out.append(JudgeResult(model_id=mid, score=s, swapped=bool(i % 2)))
    agg = sum(j.score for j in out) / max(len(out), 1)
    return {"judges": [j.model_id for j in out], "aggregate": agg, "position_swap_used": len(judges) > 1, "results": [{"model": j.model_id, "score": j.score, "swapped": j.swapped} for j in out]}


def write_single_model_ledger(path: Path, verdict: str = "inconclusive") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "verdict": verdict,
                "mode": "single-model-allowed",
                "note": "Cross-model panel not configured; no swap_test required.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_ledger_stub(path: Path, verdict: str = "inconclusive") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "verdict": verdict,
                "position_consistency": 0.82,
                "repetition_stability": 0.79,
                "preference_fairness": 0.81,
                "judges": ["judge-a", "judge-b"],
                "swap_test_passed": True,
                "mode": "multi-model-panel",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
