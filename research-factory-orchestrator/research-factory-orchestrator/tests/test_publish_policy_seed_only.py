"""Publish policy gates (collection-result seed_only)."""
from __future__ import annotations

import unittest

from runtime.publish_policy import load_publish_policy, decide_publish_allowed
from runtime.util import skill_root


class TestPublishPolicySeedOnly(unittest.TestCase):
    def test_seed_only_collection_blocks_publish(self):
        pol = load_publish_policy(skill_root())
        ok, reason = decide_publish_allowed(
            policy=pol,
            run_mode="research",
            manual_fallback=False,
            provider_pass=True,
            any_failed=False,
            external=True,
            stub_only=False,
            collection_seed_only=True,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "collection_seed_only_block")


if __name__ == "__main__":
    unittest.main()
