#!/usr/bin/env python3
"""
Reality Check: closure invariant (v19.0.3).

Default verdict = NEEDS_WORK. Pass possible only if:
  - all required artifacts exist
  - explicit semantic fail-closed fields hold
  - V1 schema validation passes for each stub (A4)
  - rollback is idempotent across repeated runs (A5)
  - no-delivery invariant holds on pristine path (A6)

Name kept as `_smoke_rollback_creates_stubs.py` for traceability with
v19.0.2 plan + release notes references; semantic intent = Reality Check.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

V1DIR = ROOT / "validators" / "core"
CORE_SCHEMAS = ROOT / "schemas" / "core"


def _run_validate(rd: Path, profile: str = "mvr") -> int:
    env = {**os.environ, "RFO_V19_PROFILE": profile, "PYTHONDONTWRITEBYTECODE": "1"}
    code = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "from runtime.validate_impl import validate; "
        "sys.exit(validate(Path(sys.argv[1])))"
    )
    p = subprocess.run(
        [sys.executable, "-S", "-c", code, str(rd)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return p.returncode


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _v1_validate(instance: object, schema_name: str) -> list[tuple[str, str]]:
    sys.path.insert(0, str(V1DIR))
    from v19_stdlib_schema_walk import validate_instance  # noqa: E402

    sp = CORE_SCHEMAS / f"{schema_name}.schema.json"
    schema = json.loads(sp.read_text(encoding="utf-8"))
    return validate_instance(instance, schema, strict_additional=True)


def _state_ok(state: str) -> bool:
    sm = json.loads((ROOT / "contracts" / "state-machine.json").read_text(encoding="utf-8"))
    states = [str(s) for s in (sm.get("states") or [])]
    return state in states


def _no_delivery_prefix_violations(obj: object, prefix: tuple[str, ...] = ("tg:", "webhook:", "email:")) -> list[str]:
    bad: list[str] = []

    def walk(x: object, path: str) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(x, list):
            for i, it in enumerate(x):
                walk(it, f"{path}[{i}]")
        elif isinstance(x, str):
            low = x.lower()
            for p in prefix:
                if low.startswith(p):
                    bad.append(f"{path}={x!r}")

    walk(obj, "")
    return bad


def _assert_stubs(rd: Path) -> None:
    required = (
        "validation-transcript.json",
        "validation-profile-used.json",
        "delivery-manifest.json",
        "final-answer-gate.json",
        "runtime-status.json",
    )
    for n in required:
        assert (rd / n).is_file(), f"missing stub: {n}"

    stub_html = rd / "report" / "rollback-stub.html"
    assert stub_html.is_file(), "missing physical rollback-stub.html (J4)"

    vt = _load_json(rd / "validation-transcript.json")
    assert vt.get("status") == "fail", "validation-transcript.status must be fail after rollback path"

    rs = _load_json(rd / "runtime-status.json")
    assert rs.get("state") == "validation_failed"
    assert _state_ok(rs["state"]), "runtime-status.state not in state-machine.json"

    dm = _load_json(rd / "delivery-manifest.json")
    assert dm.get("delivery_status") == "validation_failed"
    assert dm.get("real_external_delivery") is False
    assert dm.get("external_delivery_claim_allowed") is False
    assert dm.get("artifact_ready_claim_allowed") is False
    assert dm.get("publish_allowed") is False

    fag = _load_json(rd / "final-answer-gate.json")
    assert fag.get("passed") is False
    assert fag.get("status") == "fail"

    att = dm.get("attachments")
    assert isinstance(att, list) and len(att) >= 1
    for row in att:
        if isinstance(row, dict) and row.get("path"):
            rel = Path(str(row["path"]))
            if not rel.is_absolute():
                assert (rd / rel).is_file(), f"attachment path missing on disk: {row['path']}"

    # A6 pristine no-delivery invariant
    ack = dm.get("provider_ack_id")
    assert ack in (None, "", []), f"provider_ack_id must be empty; got {ack!r}"
    da = dm.get("delivery_attempts")
    if da is not None:
        assert da == [], f"delivery_attempts must be empty list if present; got {da!r}"
    badp = _no_delivery_prefix_violations(dm)
    assert not badp, f"A6 prefix violations: {badp}"

    # A4 V1 schema checks
    for name, key in (
        ("delivery-manifest", "delivery-manifest.json"),
        ("final-answer-gate", "final-answer-gate.json"),
        ("validation-transcript", "validation-transcript.json"),
    ):
        errs = _v1_validate(_load_json(rd / key), name)
        assert not errs, f"V1 schema fail {name}: {errs[:8]}"

    # runtime-status is not a full schemas/core file name — spot-check state only (covered above)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rfo-rollback-smoke-") as td:
        rd = Path(td)
        rc1 = _run_validate(rd, "mvr")
        assert rc1 != 0, "expected validate to fail on pristine empty run-dir"
        _assert_stubs(rd)

        rc2 = _run_validate(rd, "mvr")
        assert rc1 == rc2, f"idempotency: rc differs ({rc1} vs {rc2})"
        _assert_stubs(rd)

    print(json.dumps({"status": "pass", "issue_code": "", "detail": "rollback closure + idempotency + V1 + A6"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(json.dumps({"status": "fail", "issue_code": "ROLLBACK-SMOKE", "detail": str(e)}, ensure_ascii=False))
        raise SystemExit(1)
