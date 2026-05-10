#!/usr/bin/env python3
"""Reference parser for stdout handoff capsules.

Purpose:
- Keep a canonical implementation in this repository (R1 from remaining plan).
- Downstream host gateways can copy this logic when integrating RFO handoff parsing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HANDOFF_STDOUT_PREFIX = "__RFO_SKILL_AGENT_HANDOFF__="


def extract_last_handoff_line(stdout_text: str) -> str | None:
    """Return the payload text after prefix from the last matching non-empty line."""
    lines = [ln.strip() for ln in stdout_text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith(HANDOFF_STDOUT_PREFIX):
            return ln[len(HANDOFF_STDOUT_PREFIX) :].strip()
    return None


def parse_handoff_payload(stdout_text: str) -> dict:
    """Parse the last valid handoff payload from stdout.

    Raises:
        ValueError: when marker is absent or payload is invalid JSON object.
    """
    raw = extract_last_handoff_line(stdout_text)
    if not raw:
        raise ValueError("handoff marker not found in stdout lines")
    try:
        obj = json.loads(raw)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"handoff payload is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("handoff payload JSON must be an object")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description="Reference handoff stdout parser")
    ap.add_argument("--stdout-file", required=True, help="Path to captured stdout text file")
    args = ap.parse_args()
    txt = Path(args.stdout_file).read_text(encoding="utf-8")
    payload = parse_handoff_payload(txt)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

