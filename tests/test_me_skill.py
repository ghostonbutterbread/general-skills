from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "me" / "SKILL.md"


class MeSkillTests(unittest.TestCase):
    def test_atme_skill_is_a_compact_current_work_briefing(self) -> None:
        content = SKILL.read_text(encoding="utf-8")

        self.assertIn("name: me", content)
        self.assertIn("/atme", content)
        self.assertIn("@me", content)
        self.assertIn("current conversation", content)
        self.assertIn("session_search", content)
        self.assertIn("no more than four bullets", content)


if __name__ == "__main__":
    unittest.main()
