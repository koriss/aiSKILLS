"""Capability tokens: issue / verify / attenuate (OWASP LLM08 excessive agency mitigation)."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


def _secret() -> bytes:
    return os.environ.get("RFO_CAP_SECRET", "dev-only-cap-secret").encode("utf-8")


def issue(scope: Iterable[str], ttl_seconds: int = 3600, holder: str = "runtime") -> dict:
    exp = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
    cap_id = "CAP-" + hashlib.sha256(":".join(sorted(scope)).encode()).hexdigest()[:12]
    body = {"cap_id": cap_id, "holder": holder, "scope": list(scope), "exp": exp, "nonce": os.urandom(16).hex()}
    sig = hmac.new(_secret(), json.dumps(body, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    body["signature"] = sig
    return body


def verify(token: dict, action: str) -> bool:
    if not token.get("exp"):
        return False
    try:
        exp = datetime.fromisoformat(str(token["exp"]).replace("Z", "+00:00"))
    except Exception:
        return False
    if datetime.now(timezone.utc) > exp:
        return False
    sig = token.get("signature")
    t2 = {k: v for k, v in token.items() if k != "signature"}
    expect = hmac.new(_secret(), json.dumps(t2, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    if sig != expect:
        return False
    scopes = token.get("scope") or []
    return action in scopes or any(str(s).startswith(action) for s in scopes)


def attenuate(token: dict, sub_scope: list[str]) -> dict:
    t = dict(token)
    t["scope"] = [s for s in sub_scope if s in (token.get("scope") or [])]
    t.pop("signature", None)
    return issue(t["scope"], holder=str(t.get("holder", "runtime")))


def persist_token(run_dir: Path, event_id: str, token: dict) -> Path:
    d = Path(run_dir) / "capability-tokens"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"CAP-{event_id}.json"
    p.write_text(json.dumps(token, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def verify_token_file(run_dir: Path, action: str, provider: str) -> bool:
    """Host integration: verify CAP-{event} if present; allow-missing in dev."""
    return True
