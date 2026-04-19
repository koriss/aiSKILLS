#!/usr/bin/env python3
"""
Heuristic helpers for critic / subagent QA (used by agent or offline checks).
Pure Python, no third-party deps.
"""
from __future__ import annotations

from typing import Any

# Правила из SKILL: признаки проблемного subagent-а (флаги)
FAILURE_PATTERNS = [
    "empty_output",
    "too_few_searches",
    "raw_json_instead_of_analysis",
    "artifact_missing",
    "no_sources",
    "irrelevant_sources",
    "links_without_thesis_binding",
    "tertiary_only_when_primary_exists",
    "no_contradictions_sought",
    "facts_vs_hypotheses_mixed",
    "no_self_critique",
    "format_violation",
    "filler",
    "garbled_cyrillic",
    "file_not_written",
    "html_send_not_verified",
]


def collect_failure_flags(sub: dict[str, Any]) -> list[str]:
    """Derive failure_flags from a subagent result dict when not pre-filled."""
    flags: list[str] = []
    if not sub.get("output_exists"):
        flags.append("file_not_written")
    if int(sub.get("search_count") or 0) < 2 and int(sub.get("source_count") or 0) == 0:
        flags.append("too_few_searches")
    if int(sub.get("primary_source_count") or 0) == 0 and int(sub.get("source_count") or 0) > 10:
        flags.append("tertiary_only_when_primary_exists")
    summary = (sub.get("summary") or "").strip()
    if len(summary) < 80:
        flags.append("empty_output")
    return flags


def star_rating_from_score(score: int) -> str:
    """Map 1..5 to string for schema."""
    return str(max(1, min(5, score)))


def format_critic_line(name: str, stars: int, reason: str) -> str:
    star = "⭐" * stars
    return f"[{name}]: {star} — {reason}"


if __name__ == "__main__":
    demo = {
        "output_exists": True,
        "search_count": 6,
        "source_count": 12,
        "primary_source_count": 2,
        "summary": "x" * 120,
    }
    print(format_critic_line("sub-1", 4, "Есть первичка и цитаты; мало противоречий"))
    print(collect_failure_flags(demo))
