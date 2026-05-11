"""CLI integration surfaces for relay bridge guards (agent-owned config)."""
from __future__ import annotations

import http.server
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


class TestBridgeCliIntegration(unittest.TestCase):
    def test_empty_relay_exits_2_no_mvr_scaffold_hints(self):
        skill = _skill_root()
        script = skill / "scripts" / "run_rfo_with_web_search.py"

        class _EmptyRelay(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path.startswith("/search"):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"results": []}')
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *_args) -> None:
                pass

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _EmptyRelay)
        host, port = httpd.server_address
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

        base = f"http://{host}:{port}"
        env = {**os.environ}
        env.pop("RFO_ALLOW_MVR_EMPTY_RELAY", None)
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        try:
            with tempfile.TemporaryDirectory() as tmp:
                runs = Path(tmp) / "rfo-runs"
                runs.mkdir(parents=True, exist_ok=True)
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-S",
                        str(script),
                        "--runs-root",
                        str(runs),
                        "--task",
                        "integration empty relay",
                        "--profile",
                        "dossier",
                        "--web-search-json-api-base",
                        base,
                    ],
                    cwd=str(skill),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
        finally:
            httpd.shutdown()
            httpd.server_close()

        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        err = proc.stderr or ""
        self.assertNotIn("Relax with --profile mvr", err)
        self.assertNotIn("RFO_ALLOW_MVR_EMPTY_RELAY", err)
        self.assertIn("Relay fanout returned zero", err)

    def test_allow_gate_stub_requires_experiment_exit_2(self):
        skill = _skill_root()
        script = skill / "scripts" / "run_rfo_with_web_search.py"
        env = {**os.environ}
        env.pop("RFO_EXPERIMENT_BRIDGE", None)
        env.pop("RFO_SMOKE", None)
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(script),
                    "--runs-root",
                    str(runs),
                    "--task",
                    "x",
                    "--allow-gate-stub",
                    "--web-search-json-api-base",
                    "http://127.0.0.1:9",
                ],
                cwd=str(skill),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(proc.returncode, 2)
        self.assertIn("RFO_EXPERIMENT_BRIDGE", proc.stderr or "")
