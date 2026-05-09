"""Tests for user-facing Markdown deliverables and facts gate."""
from __future__ import annotations

import unittest

from runtime.chat_md import apply_facts_gate


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


if __name__ == "__main__":
    unittest.main()
