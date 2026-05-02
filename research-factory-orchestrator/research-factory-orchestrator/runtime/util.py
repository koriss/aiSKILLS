"""Shared helpers and constants for RFO runtime modules."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUSES = [
    "confirmed",
    "probable",
    "partial",
    "disputed",
    "contradicted",
    "false",
    "unsupported",
    "unknown",
    "stale",
    "inferred",
]
REQ_EVENTS = ["OUT-0001", "OUT-0002", "OUT-0003", "OUT-0004", "OUT-0005", "OUT-0006"]
CHAT = [
    ("OUT-0001", "analytical_memo", "chat/message-001-analytical-memo.txt"),
    ("OUT-0002", "factual_dossier", "chat/message-002-facts.txt"),
    ("OUT-0003", "io_propaganda_check", "chat/message-003-io-propaganda-check.txt"),
    ("OUT-0004", "files_and_delivery_status", "chat/message-004-files.txt"),
]
PKG_REQUIRED = [
    "run.json",
    "run-catalog-entry.json",
    "entrypoint-proof.json",
    "runtime-status.json",
    "observability-events.jsonl",
    "trace.jsonl",
    "feature-truth-matrix.json",
    "work-queue/work-unit-ledger.json",
    "late-results-ledger.jsonl",
    "amendment-ledger.jsonl",
    "interface/interface-request.json",
    "interface/normalized-command.json",
    "jobs/runtime-job.json",
    "graph/target-graph.json",
    "graph/entity-registry.json",
    "graph/edge-ledger.json",
    "graph/frontier.json",
    "graph/wave-plan.json",
    "graph/wave-events.jsonl",
    "claims/claims-registry.json",
    "claims/claim-status-ledger.json",
    "evidence/evidence-cards.json",
    "sources/sources.json",
    "sources/source-quality.json",
    "sources/source-conflict-matrix.json",
    "sources/source-laundering.json",
    "synthesis/synthesis-events.jsonl",
    "synthesis/open-questions.json",
    "synthesis/evidence-debt.json",
    "synthesis/contradiction-matrix.json",
    "io/io-method-matches.json",
    "io/narrative-map.json",
    "io/source-laundering-map.json",
    "io/amplification-chain.json",
    "self-audit/runtime-self-audit.json",
    "self-audit/model-compliance-ledger.json",
    "self-audit/search-quality-ledger.json",
    "self-audit/deviation-ledger.json",
    "self-audit/hallucination-risk-map.json",
    "report/analytical-memo.json",
    "report/factual-dossier.json",
    "report/io-propaganda-check.json",
    "report/semantic-report.json",
    "report/full-report.html",
    "chat/chat-message-plan.json",
    "chat/message-001-analytical-memo.txt",
    "chat/message-002-facts.txt",
    "chat/message-003-io-propaganda-check.txt",
    "chat/message-004-files.txt",
    "delivery-manifest.json",
    "attachment-ledger.json",
    "final-answer-gate.json",
    "artifact-manifest.json",
    "provenance-manifest.json",
    "validation-transcript.json",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(s: str) -> str:
    s = (s or "research").lower()
    table = str.maketrans(
        {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }
    )
    s = s.translate(table)
    s = re.sub(r"https?://\S+", " link ", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "research"
    return s[:56].strip("_") or "research"


def sid(prefix: str, *parts: object) -> str:
    return prefix + "-" + hashlib.sha256("\n".join(map(str, parts)).encode()).hexdigest()[:12]


def jw(p: Path | str, o: object) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jr(p: Path | str, d: object | None = None):
    p = Path(p)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {} if d is None else d


def tw(p: Path | str, t: str) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding="utf-8")


def jl(p: Path | str, o: object) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.open("a", encoding="utf-8").write(json.dumps(o, ensure_ascii=False) + "\n")


def sha(p: Path | str) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1048576), b""):
            h.update(c)
    return h.hexdigest()


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent
