"""Optional Merkle batch anchor over trace/handoff batches (RFC 9162 / SCITT prep)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def merkle_root(leaves: Iterable[str]) -> str:
    layer = [hashlib.sha256(x.encode()).hexdigest() for x in leaves]
    if not layer:
        return "0" * 64
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [hashlib.sha256((layer[i] + layer[i + 1]).encode()).hexdigest() for i in range(0, len(layer), 2)]
    return layer[0]


def write_anchor(run_dir: Path, lines: list[str], tree_size: int | None = None) -> Path:
    run_dir = Path(run_dir)
    out = run_dir / "self-audit" / "merkle-anchor.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    root = merkle_root(lines)
    payload = {"tree_size": tree_size or len(lines), "root_hash": root, "epoch": len(lines), "note": "external anchoring hook reserved"}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
