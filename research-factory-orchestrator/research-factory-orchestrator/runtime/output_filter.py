"""Application-side output filtering (not model-side). arXiv:2604.23887."""
from __future__ import annotations

import base64
import re
from pathlib import Path

_INJECTION_RE = re.compile(
    r"(?i)(ignore\s+previous|disregard\s+above|system\s*[:=]|<\|im_start\|>|\\u202e|override\s+instructions|"
    r"new\s+instructions\s*:|you\s+are\s+now\s+)",
)
_HIDDEN_HTML = re.compile(r"(?i)(<script\b|</script>|onerror\s*=|javascript\s*:)",)


def scan_text(text: str) -> list[str]:
    hits: list[str] = []
    if _INJECTION_RE.search(text):
        hits.append("injection_pattern")
    if _HIDDEN_HTML.search(text):
        hits.append("hidden_html_or_script")
    # Suspicious large base64 blob without MIME context
    for m in re.finditer(r"[A-Za-z0-9+/]{200,}={0,2}", text):
        raw = m.group(0)
        try:
            if len(base64.b64decode(raw, validate=True)) > 512:
                hits.append("large_base64_blob")
                break
        except Exception:
            continue
    return hits


def assert_safe_payload(text: str) -> None:
    h = scan_text(text)
    if h:
        raise ValueError("unsafe_payload:" + ",".join(h))


def filter_file(path: Path) -> None:
    t = path.read_text(encoding="utf-8", errors="replace")
    assert_safe_payload(t)
