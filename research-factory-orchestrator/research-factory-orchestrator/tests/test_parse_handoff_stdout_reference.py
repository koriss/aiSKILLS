from __future__ import annotations

import unittest

from scripts.parse_handoff_stdout_reference import (
    extract_last_handoff_line,
    parse_handoff_payload,
)


class TestParseHandoffStdoutReference(unittest.TestCase):
    def test_extract_last_handoff_line(self) -> None:
        txt = "\n".join(
            [
                "progress 1",
                "__RFO_SKILL_AGENT_HANDOFF__={\"run_id\":\"A\"}",
                "wrapper noise",
                "__RFO_SKILL_AGENT_HANDOFF__={\"run_id\":\"B\",\"status\":\"ok\"}",
                "",
            ]
        )
        self.assertEqual(
            extract_last_handoff_line(txt),
            "{\"run_id\":\"B\",\"status\":\"ok\"}",
        )

    def test_parse_handoff_payload_valid(self) -> None:
        txt = "__RFO_SKILL_AGENT_HANDOFF__={\"run_id\":\"X\",\"status\":\"ok\"}\n"
        obj = parse_handoff_payload(txt)
        self.assertEqual(obj.get("run_id"), "X")
        self.assertEqual(obj.get("status"), "ok")

    def test_parse_handoff_payload_missing_marker(self) -> None:
        with self.assertRaises(ValueError):
            parse_handoff_payload("plain text only\n")


if __name__ == "__main__":
    unittest.main()

