"""Regression coverage for human-actionable outreach."""
from pathlib import Path
import unittest

SKILL = Path(__file__).resolve().parents[1] / 'skills/agent-outreach/SKILL.md'

class ActionableHandoffTests(unittest.TestCase):
    def test_human_handoff_is_proactive_and_self_contained(self):
        text = SKILL.read_text(encoding='utf-8').lower()
        for required in (
            'send the outreach when a human handoff is ready',
            'exact reachable handoff url',
            'specific action',
            'account or role',
            'fallback',
            'expiry',
            'how to signal completion',
            'who can access the handoff service',
            'if no monitored completion channel is known',
            'do not invent',
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

if __name__ == '__main__':
    unittest.main()
