#!/usr/bin/env python3
import json
import sys
import tempfile
from pathlib import Path
REQUIRED_MD_HEADINGS = [
    "## Executive Summary",
    "## Question Framing",
    "## Established Facts",
    "## Key Claims and Verification Status",
    "## Timeline",
    "## Actors, Interests, and Capabilities",
    "## Evidence Map",
    "## Competing Hypotheses",
    "## Non-Obvious Links and Hidden Incentives",
    "## Risks, Opportunities, and Second-Order Effects",
    "## Forecast and Signposts",
    "## Bottom Line",
    "## Confidence and Unknowns",
    "## Sources"
]
REQUIRED_JSON_KEYS = [
    "status",
    "main_answer",
    "executive_summary",
    "established_facts",
    "key_claims",
    "timeline",
    "actors",
    "hypotheses",
    "non_obvious_links",
    "risks",
    "forecast",
    "unknowns",
    "confidence",
    "sources"
]
VALID_STATUS = {"complete", "partial", "insufficient_evidence"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}
VALID_CLAIM_STATUS = {"confirmed", "false", "misleading", "unverified", "mixed", "out-of-context"}
def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)
def ok(message: str) -> None:
    print(f"OK: {message}")
    sys.exit(0)
def validate_markdown(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [h for h in REQUIRED_MD_HEADINGS if h not in text]
    if missing:
        fail(f"Markdown report missing headings: {', '.join(missing)}")
    ok(f"markdown report validated: {path}")
def validate_json_report(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_JSON_KEYS if k not in data]
    if missing:
        fail(f"JSON report missing keys: {', '.join(missing)}")
    if data["status"] not in VALID_STATUS:
        fail("Invalid status value")
    if not isinstance(data["main_answer"], str) or not data["main_answer"].strip():
        fail("main_answer must be a non-empty string")
    if not isinstance(data["executive_summary"], list):
        fail("executive_summary must be a list")
    if not isinstance(data["established_facts"], list):
        fail("established_facts must be a list")
    if not isinstance(data["key_claims"], list):
        fail("key_claims must be a list")
    if not isinstance(data["timeline"], list):
        fail("timeline must be a list")
    if not isinstance(data["actors"], list):
        fail("actors must be a list")
    if not isinstance(data["hypotheses"], list):
        fail("hypotheses must be a list")
    if not isinstance(data["non_obvious_links"], list):
        fail("non_obvious_links must be a list")
    if not isinstance(data["risks"], list):
        fail("risks must be a list")
    if not isinstance(data["forecast"], list):
        fail("forecast must be a list")
    if not isinstance(data["unknowns"], list):
        fail("unknowns must be a list")
    if not isinstance(data["confidence"], dict):
        fail("confidence must be an object")
    if not isinstance(data["sources"], dict):
        fail("sources must be an object")
    confidence = data["confidence"]
    if confidence.get("overall") not in VALID_CONFIDENCE:
        fail("confidence.overall must be High, Medium, or Low")
    if not isinstance(confidence.get("rationale"), str) or not confidence["rationale"].strip():
        fail("confidence.rationale must be a non-empty string")
    sources = data["sources"]
    for key in ["primary", "secondary", "contextual"]:
        if key not in sources or not isinstance(sources[key], list):
            fail(f"sources.{key} must exist and be a list")
    for item in data["key_claims"]:
        if not isinstance(item, dict):
            fail("each key_claim must be an object")
        if item.get("status") not in VALID_CLAIM_STATUS:
            fail("invalid key_claim status")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            fail("key_claim.claim must be a non-empty string")
        if not isinstance(item.get("evidence"), list):
            fail("key_claim.evidence must be a list")
    for item in data["timeline"]:
        if not isinstance(item, dict):
            fail("each timeline item must be an object")
        if not isinstance(item.get("date"), str) or not item["date"].strip():
            fail("timeline.date must be a non-empty string")
        if not isinstance(item.get("event"), str) or not item["event"].strip():
            fail("timeline.event must be a non-empty string")
    for item in data["actors"]:
        if not isinstance(item, dict):
            fail("each actor must be an object")
        for key in ["name", "interests", "capabilities", "constraints"]:
            if key not in item:
                fail(f"actor missing key: {key}")
    for item in data["hypotheses"]:
        if not isinstance(item, dict):
            fail("each hypothesis must be an object")
        for key in ["id", "summary", "support", "contradictions", "assumptions", "confidence"]:
            if key not in item:
                fail(f"hypothesis missing key: {key}")
        if item["confidence"] not in VALID_CONFIDENCE:
            fail("hypothesis.confidence must be High, Medium, or Low")
    ok(f"json report validated: {path}")
def run_selftest() -> None:
    root = Path(__file__).resolve().parents[1]
    md_path = root / "examples" / "example-report.md"
    json_path = root / "examples" / "example-report.json"
    validate_markdown(md_path)
    # validate_markdown exits on success; so we need a direct call pattern
    # use an alternate branch instead:
    pass
def selftest() -> None:
    root = Path(__file__).resolve().parents[1]
    md_path = root / "examples" / "example-report.md"
    json_path = root / "examples" / "example-report.json"
    text = md_path.read_text(encoding="utf-8")
    missing = [h for h in REQUIRED_MD_HEADINGS if h not in text]
    if missing:
        fail(f"Selftest failed for markdown example, missing headings: {', '.join(missing)}")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_JSON_KEYS if k not in data]
    if missing:
        fail(f"Selftest failed for json example, missing keys: {', '.join(missing)}")
    if data["status"] not in VALID_STATUS:
        fail("Selftest failed: invalid status in example JSON")
    if data["confidence"]["overall"] not in VALID_CONFIDENCE:
        fail("Selftest failed: invalid confidence in example JSON")
    print(f"OK: markdown example validated: {md_path}")
    print(f"OK: json example validated: {json_path}")
    print("OK: selftest passed")
    sys.exit(0)
def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
    if len(sys.argv) != 2:
        fail("Usage: python3 validate_report.py <report.md|report.json> OR --selftest")
    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"File not found: {path}")
    if path.suffix.lower() == ".md":
        validate_markdown(path)
    elif path.suffix.lower() == ".json":
        validate_json_report(path)
    else:
        fail("Unsupported file type. Use .md or .json")
if __name__ == "__main__":
    main()
