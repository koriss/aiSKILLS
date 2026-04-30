#!/usr/bin/env python3
from pathlib import Path
import argparse, sys, re

REQUIRED_PATTERNS = {
    "executive_summary": r'id=["\']executive-summary["\']|Executive Summary|Кратк',
    "research_question_scope": r'id=["\']research-question-scope["\']|Research Question|Scope|Вопрос|Область',
    "methodology": r'id=["\']methodology["\']|Methodology|Методолог',
    "search_strategy": r'id=["\']search-strategy["\']|Search Strategy|Стратегия поиска',
    "source_quality": r'id=["\']source-quality["\']|Source Quality|качество источ',
    "evidence_map": r'id=["\']evidence-map["\']|Evidence Map|карта доказ',
    "verified_claims": r'id=["\']verified-claims["\']|Verified Claims|подтвержд',
    "uncertain_claims": r'id=["\']uncertain-claims["\']|Uncertain|Disputed|спорн|неопредел',
    "fact_check": r'id=["\']fact-check["\']|Fact-Check|фактчек',
    "citation_locator": r'id=["\']citation-locator["\']|Citation|источник|якор',
    "adversarial_review": r'id=["\']adversarial-review["\']|Adversarial|критическ',
    "error_audit": r'id=["\']error-audit["\']|Error Audit|аудит ошибок',
    "known_gaps": r'id=["\']known-gaps["\']|Known Gaps|ограничен|пробел',
    "sources": r'id=["\']sources["\']|Sources|Источники'
}

PLACEHOLDERS = ["{{", "TODO", "TBD", "PLACEHOLDER", "pending template"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_report")
    ap.add_argument("--min-bytes", type=int, default=2000)
    args = ap.parse_args()

    p = Path(args.html_report)
    errors = []
    if not p.exists():
        errors.append("html report missing")
    elif p.stat().st_size < args.min_bytes:
        errors.append(f"html report too small: {p.stat().st_size} bytes")
    else:
        txt = p.read_text(encoding="utf-8", errors="replace")
        low = txt.lower()
        if "<html" not in low or "</html>" not in low:
            errors.append("not standalone HTML")
        for name, pattern in REQUIRED_PATTERNS.items():
            if not re.search(pattern, txt, re.I):
                errors.append(f"missing section: {name}")
        for ph in PLACEHOLDERS:
            if ph.lower() in low:
                errors.append(f"placeholder text present: {ph}")
        if "http://" not in low and "https://" not in low and "source" not in low and "источник" not in low:
            errors.append("no visible source references")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: html report validates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
