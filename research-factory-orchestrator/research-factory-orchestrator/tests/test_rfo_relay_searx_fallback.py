"""SearXNG relay: GET→HTML triggers POST JSON fallback; collector relay packet flags."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.rfo_relay_search_helpers import relay_json_search


class TestRelayJsonSearch(unittest.TestCase):
    def test_post_fallback_when_get_returns_html(self) -> None:
        html = b"<!DOCTYPE html><html><head></head><body>ui</body></html>"
        good = json.dumps(
            {
                "results": [
                    {"url": "https://example.com/a", "title": "A", "content": "snippet a"},
                    {"url": "https://example.com/b", "title": "B", "content": "snippet b"},
                ]
            }
        ).encode("utf-8")

        class _Resp:
            def __init__(self, body: bytes, ctype: str = "text/html") -> None:
                self._body = body
                self.headers = {"Content-Type": ctype}

            def read(self) -> bytes:
                return self._body

            def __enter__(self) -> "_Resp":
                return self

            def __exit__(self, *exc: object) -> None:
                return None

        _n = [0]

        def fake_urlopen(_req: object, **_kwargs: object) -> _Resp:
            _n[0] += 1
            if _n[0] == 1:
                return _Resp(html, "text/html")
            return _Resp(good, "application/json")

        with mock.patch(
            "scripts.rfo_relay_search_helpers.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            rows, meta = relay_json_search(
                "http://127.0.0.1:9",
                "test query",
                5,
                user_agent="RFO-test/0",
                timeout=3.0,
            )
        self.assertTrue(meta.get("post_fallback"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["url"], "https://example.com/a")


class TestCollectorRelayPacket(unittest.TestCase):
    def test_relay_prefetch_packet_sets_web_flags(self) -> None:
        from runtime.collector import collect

        with tempfile.TemporaryDirectory() as tmp:
            rd = Path(tmp) / "run1"
            rd.mkdir(parents=True, exist_ok=True)
            pkt = rd / "packet.json"
            pkt.write_text(
                json.dumps(
                    {
                        "relay_prefetch_bridge": True,
                        "sources": [
                            {
                                "source_id": "SRC-1",
                                "title": "t",
                                "canonical_origin_id": "https://ex.org/x",
                                "url": "https://ex.org/x",
                                "verification_mode": "testimony",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            env = {
                "RFO_SOURCE_PACKET": str(pkt),
                "RFO_EXTERNAL_COLLECTION": "optional",
                "RFO_NO_NETWORK": "",
            }
            with mock.patch.dict("os.environ", env, clear=False):
                summary = collect(rd, run_id="RUN", job_id="JOB", profile="dossier")
        self.assertTrue(summary.get("web_search_attempted"))
        self.assertTrue(summary.get("external_web_search_executed"))
        self.assertEqual(int(summary.get("web_search_result_count") or 0), 1)
        self.assertIn("relay_prefetch", str(summary.get("backend_reason") or ""))


if __name__ == "__main__":
    unittest.main()
