"""Schema-safe defaults for fail-closed rollback and smoke stubs (v19.0.2+)."""
from __future__ import annotations

from typing import Any

from runtime.util import now

ZERO64 = "0" * 64


def merge_rollback_delivery_manifest(dm: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of delivery-manifest with validation-failed rollback fields (schema-safe)."""
    out: dict[str, Any] = dict(dm)
    out.update(
        {
            "delivery_status": "validation_failed",
            "real_external_delivery": False,
            "artifact_ready_claim_allowed": False,
            "external_delivery_claim_allowed": False,
            "stub_delivery": True,
            "stub_delivery_disclosure_required": True,
            "delivery_claim_allowed": False,
            "publish_allowed": False,
            "publish_reason": "validation_failed",
            "updated_at": now(),
        }
    )
    atts = out.get("attachments")
    if not isinstance(atts, list) or len(atts) == 0:
        out["attachments"] = [{"path": "report/rollback-stub.html", "sha256": ZERO64}]
    return out


def merge_rollback_final_answer_gate(fg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(fg)
    out.update({"passed": False, "status": "fail", "updated_at": now()})
    return out
