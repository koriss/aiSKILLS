"""CLI integration surfaces for relay bridge guards (agent-owned config)."""
from __future__ import annotations

import http.server
import json
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
        env["RFO_RUN_EXECUTION_MODE"] = "test_fixture"
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

    def test_preflight_emits_effective_config_json_exit_0(self):
        skill = _skill_root()
        script = skill / "scripts" / "run_rfo_with_web_search.py"
        env = {**os.environ}
        env.pop("RFO_EXPERIMENT_BRIDGE", None)
        env.pop("RFO_SMOKE", None)
        env.pop("RFO_ALLOW_LEGACY_ENTRYPOINT", None)
        env["RFO_RUN_EXECUTION_MODE"] = "test_fixture"
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        class _OkRelay(http.server.BaseHTTPRequestHandler):
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

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _OkRelay)
        host, port = httpd.server_address
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://{host}:{port}"

        try:
            with tempfile.TemporaryDirectory() as tmp:
                runs = Path(tmp) / "rfo-runs"
                runs.mkdir(parents=True, exist_ok=True)
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-S",
                        str(script),
                        "--preflight",
                        "--runs-root",
                        str(runs),
                        "--task",
                        "preflight-only",
                        "--web-search-json-api-base",
                        base,
                    ],
                    cwd=str(skill),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
        finally:
            httpd.shutdown()
            httpd.server_close()

        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        doc = json.loads(proc.stdout or "{}")
        self.assertEqual(doc.get("schema"), "rfo-effective-config-v1")
        self.assertEqual(doc.get("entrypoint"), "scripts/run_rfo_with_web_search.py")
        self.assertEqual(doc.get("runs_root"), str(runs.resolve()))
        self.assertTrue(doc.get("relay_chain"))
        self.assertTrue(doc.get("relay_reachable"))

    def test_preflight_unreachable_relay_exit_2(self):
        """JSON relay that refuses TCP → preflight exit 2 + relay_unreachable."""
        skill = _skill_root()
        script = skill / "scripts" / "rfo_execute.py"
        env = {**os.environ}
        for k in ("RFO_SMOKE", "RFO_EXPERIMENT_BRIDGE", "RFO_ALLOW_LEGACY_ENTRYPOINT"):
            env.pop(k, None)
        env["RFO_RUN_EXECUTION_MODE"] = "test_fixture"
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(script),
                    "--preflight",
                    "--runs-root",
                    str(runs),
                    "--task",
                    "unreachable-relay",
                    "--web-search-json-api-base",
                    "http://127.0.0.1:9",
                ],
                cwd=str(skill),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        doc = json.loads(proc.stdout or "{}")
        self.assertIn("relay_unreachable", doc.get("errors") or [])
        self.assertEqual(doc.get("blocked_dependency"), "web_search_json_api_base")
        self.assertEqual(doc.get("entrypoint"), "scripts/rfo_execute.py")

    def test_preflight_forbidden_env_exit_2(self):
        skill = _skill_root()
        script = skill / "scripts" / "run_rfo_with_web_search.py"
        env = {**os.environ}
        env["RFO_SMOKE"] = "1"

        runs = Path.home() / "rfo-runs"
        runs.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                sys.executable,
                "-S",
                str(script),
                "--preflight",
                "--runs-root",
                str(runs),
                "--task",
                "x",
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
        doc = json.loads(proc.stdout or "{}")
        self.assertIn("forbidden_canonical_env", doc.get("errors") or [])

    def test_rfo_execute_preflight_same_as_bridge(self):
        skill = _skill_root()
        facade = skill / "scripts" / "rfo_execute.py"
        env = {**os.environ}
        for k in ("RFO_SMOKE", "RFO_EXPERIMENT_BRIDGE", "RFO_ALLOW_LEGACY_ENTRYPOINT"):
            env.pop(k, None)
        env["RFO_RUN_EXECUTION_MODE"] = "test_fixture"
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)

            class _OkRelay(http.server.BaseHTTPRequestHandler):
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

            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _OkRelay)
            h, p = httpd.server_address
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            relay_base = f"http://{h}:{p}"
            try:
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-S",
                        str(facade),
                        "--preflight",
                        "--runs-root",
                        str(runs),
                        "--task",
                        "via-facade",
                        "--web-search-json-api-base",
                        relay_base,
                    ],
                    cwd=str(skill),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            finally:
                httpd.shutdown()
                httpd.server_close()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        doc = json.loads(proc.stdout or "{}")
        self.assertEqual(doc.get("schema"), "rfo-effective-config-v1")
        self.assertEqual(doc.get("entrypoint"), "scripts/rfo_execute.py")
        self.assertTrue(doc.get("relay_reachable"))

    def test_preflight_missing_relay_exit_2_canonical_failfast(self):
        """Canonical bridge: no relay argv/env → non-zero preflight (not silent stub)."""
        skill = _skill_root()
        facade = skill / "scripts" / "rfo_execute.py"
        env = {**os.environ}
        for k in (
            "RFO_SMOKE",
            "RFO_EXPERIMENT_BRIDGE",
            "RFO_ALLOW_LEGACY_ENTRYPOINT",
            "RFO_WEB_SEARCH_JSON_API_BASE",
            "RFO_WEB_SEARCH_SECONDARY_JSON_API_BASE",
        ):
            env.pop(k, None)
        env["RFO_RUN_EXECUTION_MODE"] = "test_fixture"
        env["RFO_ALLOW_TMP_RUNS_ROOT"] = "1"

        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "rfo-runs"
            runs.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(facade),
                    "--preflight",
                    "--runs-root",
                    str(runs),
                    "--task",
                    "no-relay",
                ],
                cwd=str(skill),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        doc = json.loads(proc.stdout or "{}")
        self.assertEqual(doc.get("schema"), "rfo-effective-config-v1")
        self.assertIn("missing_relay", doc.get("errors") or [])
