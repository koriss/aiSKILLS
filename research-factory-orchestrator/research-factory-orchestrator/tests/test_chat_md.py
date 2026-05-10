"""Tests for user-facing Markdown deliverables and facts gate."""
from __future__ import annotations

import unittest

from runtime.chat_md import apply_facts_gate, sanitize_chat_body_for_plain_channels


class TestFactsGate(unittest.TestCase):
    def test_downgrades_confirmed_without_url(self):
        claims = [
            {
                "claim_id": "C1",
                "status": "confirmed",
                "support_set": [{"source_id": "S1", "evidence_card_id": "E1", "role_for_claim": "primary_support"}],
            }
        ]
        sources = [{"source_id": "S1", "url": "", "full_url": ""}]
        out, meta = apply_facts_gate(claims, sources)
        self.assertEqual(out[0]["status"], "unsupported")
        self.assertIn("C1", meta["downgraded_claim_ids"])
        self.assertIs(meta["confirmed_without_source_allowed"], False)

    def test_keeps_confirmed_with_url(self):
        claims = [
            {
                "claim_id": "C2",
                "status": "confirmed",
                "support_set": [{"source_id": "S2", "evidence_card_id": "E2", "role_for_claim": "primary_support"}],
            }
        ]
        sources = [{"source_id": "S2", "url": "https://example.com/a"}]
        out, meta = apply_facts_gate(claims, sources)
        self.assertEqual(out[0]["status"], "confirmed")
        self.assertEqual(meta["downgraded_claim_ids"], [])


class TestSanitizeChatBody(unittest.TestCase):
    def test_pipe_table_becomes_bullets(self):
        inp = "| A | B |\n|:---:|:---:|\n| 1 | 2 |\n| 3 | 4 |\n"
        out = sanitize_chat_body_for_plain_channels(inp)
        self.assertNotIn("|", out)
        self.assertIn("- A: 1 — B: 2", out)
        self.assertIn("- A: 3 — B: 4", out)

    def test_tree_flattened_to_bullet(self):
        inp = "    ├── foo bar\n└── baz\n"
        out = sanitize_chat_body_for_plain_channels(inp)
        self.assertNotIn("├──", out)
        self.assertIn("- foo bar", out)
        self.assertIn("- baz", out)

    def test_preserves_fenced_block(self):
        inp = "```markdown\n| a | b |\n├── x\n```\nParagraph without table syntax.\n"
        out = sanitize_chat_body_for_plain_channels(inp)
        self.assertIn("| a | b |", out)
        self.assertIn("├── x", out)
        self.assertIn("Paragraph without table syntax.", out)


if __name__ == "__main__":
    unittest.main()
