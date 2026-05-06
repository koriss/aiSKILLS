"""Minimal stdlib webhook receiver sketch (HMAC verification belongs in operator nginx/systemd layer)."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


def _verify(secret: bytes, body: bytes, header_sig: str) -> bool:
    if not secret or not header_sig:
        return False
    mac = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, header_sig.replace("sha256=", "").strip())


class Handler(BaseHTTPRequestHandler):
    server_version = "RFO-Telegram-Webhook/1.0"

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length > 0 else b""
        secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").encode()
        sig = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        ok = _verify(secret, body, sig) if secret else True
        self.send_response(200 if ok else 401)
        self.end_headers()
        out: dict[str, Any] = {"ok": ok, "path": self.path}
        self.wfile.write(json.dumps(out).encode())


def main() -> int:
    host = os.environ.get("TELEGRAM_WEBHOOK_BIND", "127.0.0.1")
    port = int(os.environ.get("TELEGRAM_WEBHOOK_PORT", "8787"))
    HTTPServer((host, port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
