#!/usr/bin/env python3
"""Mock Telegram Bot API + full smoke path; asserts HTTP trace + real delivery ack truth.

``delivery-manifest.json`` may reflect fail-closed rollback after validate while still
showing ``stub_delivery`` at the manifest rollup; this smoke therefore asserts
**per-ack** ``real_external_delivery`` on Telegram ``OUT-*`` events plus HTTP hits.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = ["OUT-0001", "OUT-0002", "OUT-0003", "OUT-0004", "OUT-0005", "OUT-0006"]


def main() -> int:
    http_hits: list[str] = []
    tg: list[dict] = []

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:  # noqa: D401
            return

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0") or 0)
            _ = self.rfile.read(length) if length > 0 else b""
            http_hits.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            mid = 9000 + len(http_hits)
            self.wfile.write(json.dumps({"ok": True, "result": {"message_id": mid}}).encode())

    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    py = sys.executable
    core = ROOT / "scripts" / "rfo_runtime_core.py"
    try:
        with tempfile.TemporaryDirectory(prefix="rfo-tg-real-") as td:
            smoke_root = Path(td)
            env = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "RFO_V19_PROFILE": "mvr",
                "TELEGRAM_API_BASE": f"http://127.0.0.1:{port}",
                "TELEGRAM_BOT_TOKEN": "fake-test-token",
                "TELEGRAM_CHAT_ID": "424242",
            }
            p = subprocess.run(
                [py, "-S", str(core), "smoke", "--runs-root", str(smoke_root), "--provider", "telegram", "--interface", "telegram"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if p.returncode != 0:
                print(
                    json.dumps(
                        {
                            "status": "fail",
                            "error": "smoke_nonzero",
                            "rc": p.returncode,
                            "stderr": (p.stderr or "")[-2000:],
                        },
                        ensure_ascii=False,
                    )
                )
                return 1
            latest = smoke_root / "index" / "latest.json"
            if not latest.is_file():
                print(json.dumps({"status": "fail", "error": "no_latest"}, ensure_ascii=False))
                return 1
            run_dir = Path(json.loads(latest.read_text(encoding="utf-8")).get("run_dir") or "")
            acks = []
            for e in REQ:
                ap = run_dir / "delivery-acks" / f"{e}.json"
                if ap.is_file():
                    acks.append(json.loads(ap.read_text(encoding="utf-8")))
            if len(http_hits) < 1:
                print(json.dumps({"status": "fail", "error": "TELEGRAM-REAL-SEND-MISSING-HTTP-TRACE", "hits": http_hits}, ensure_ascii=False))
                return 1
            tg.clear()
            tg.extend([a for a in acks if str(a.get("provider")) == "telegram"])
            if not tg or not all(a.get("real_external_delivery") is True and a.get("stub_delivery") is False for a in tg):
                print(json.dumps({"status": "fail", "error": "telegram_ack_not_real_external", "acks_sample": tg[:2]}, ensure_ascii=False))
                return 1
            ftm_path = run_dir / "feature-truth-matrix.json"
            ftm = json.loads(ftm_path.read_text(encoding="utf-8")) if ftm_path.is_file() else {}
            feats = ftm.get("features") if isinstance(ftm.get("features"), dict) else {}
            if feats.get("provider_telegram_real_send") == "stub":
                print(json.dumps({"status": "fail", "error": "TELEGRAM-AGENT-CONTRACT-VIOLATION", "features": feats}, ensure_ascii=False))
                return 1
    finally:
        srv.shutdown()
        th.join(timeout=5)
    print(
        json.dumps(
            {"status": "pass", "smoke_id": "_smoke_telegram_real_send", "http_hits": len(http_hits), "telegram_acks": len(tg)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
