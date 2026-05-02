#!/usr/bin/env python3
"""
Corrupt-render → validate → fail-closed rollback Reality Check (v19.0.4).

Builds a minimal run via adapter → worker → outbox (CLI path), injects a forbidden
``Placeholder`` marker into ``report/full-report.html`` (legacy validate gate), then
runs ``validate()`` **without** ``RFO_V19_PROFILE`` so the legacy HTML sanity path fires.
Asserts rollback artifacts: ``delivery-manifest`` fail-closed fields, ``rollback-stub.html``.
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


def main() -> int:
    core = str(ROOT / "scripts" / "rfo_v18_core.py")
    py = sys.executable
    runs_root = Path(tempfile.mkdtemp(prefix="rfo-corrupt-render-"))
    env_base = {k: v for k, v in os.environ.items() if k != "RFO_V19_PROFILE"}
    env_base["PYTHONDONTWRITEBYTECODE"] = "1"

    def run_step(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [py, "-S", core, *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env=env_base,
        )

    adapter_args = [
        "adapter",
        "--runs-root",
        str(runs_root),
        "--interface",
        "direct_runtime",
        "--provider",
        "cli",
        "--conversation-id",
        "test",
        "--message-id",
        "1",
        "--user-id",
        "me",
        "--task",
        "test internal audit target",
    ]
    for name, args in (
        ("adapter", adapter_args),
        ("worker", ["worker", "--runs-root", str(runs_root), "--mode", "research", "--execute-runtime"]),
        ("outbox", ["outbox", "--runs-root", str(runs_root)]),
    ):
        p = run_step(args)
        if p.returncode != 0:
            print(f"[corrupt_smoke] {name} failed rc={p.returncode}", file=sys.stderr)
            print((p.stderr or "")[-2000:], file=sys.stderr)
            return 1

    latest = runs_root / "index" / "latest.json"
    if not latest.is_file():
        print("[corrupt_smoke] missing index/latest.json", file=sys.stderr)
        return 1
    try:
        run_dir = Path(json.loads(latest.read_text(encoding="utf-8"))["run_dir"])
    except Exception as e:
        print(f"[corrupt_smoke] bad latest.json: {e}", file=sys.stderr)
        return 1

    rep = run_dir / "report" / "full-report.html"
    if not rep.is_file():
        print("[corrupt_smoke] missing report/full-report.html", file=sys.stderr)
        return 1
    rep.write_text(rep.read_text(encoding="utf-8") + "\n<!-- Placeholder corrupt -->\n", encoding="utf-8")

    code = (
        "import sys; from pathlib import Path; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "from runtime.validate_impl import validate; "
        "sys.exit(validate(Path(sys.argv[1])))"
    )
    pval = subprocess.run(
        [py, "-S", "-c", code, str(run_dir)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
        env=env_base,
    )
    if pval.returncode == 0:
        print("[corrupt_smoke] expected validate rc!=0", file=sys.stderr)
        return 1

    stub = run_dir / "report" / "rollback-stub.html"
    if not stub.is_file():
        print("[corrupt_smoke] missing report/rollback-stub.html after rollback", file=sys.stderr)
        return 1

    dm = json.loads((run_dir / "delivery-manifest.json").read_text(encoding="utf-8"))
    if dm.get("delivery_status") != "validation_failed":
        print(f"[corrupt_smoke] bad delivery_status: {dm.get('delivery_status')!r}", file=sys.stderr)
        return 1
    if dm.get("real_external_delivery") is not False:
        print("[corrupt_smoke] real_external_delivery must be False after rollback", file=sys.stderr)
        return 1

    print(json.dumps({"status": "pass", "run_dir": str(run_dir), "validate_rc": pval.returncode}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
