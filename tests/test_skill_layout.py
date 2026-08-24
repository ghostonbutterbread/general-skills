from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "account-manager",
    "account-tui-colors",
    "bitwarden",
    "coordination",
    "daddy",
    "faq",
    "gmail-otp",
    "hoster-ssh",
    "i-have-adhd",
    "nightly-learning",
    "papercuts",
    "resilio-sync",
    "safe-fetch",
    "script_manager",
    "skill-seeds",
    "tmux",
}
LEGACY_CATEGORY_DIRECTORIES = {"accounts", "core", "learning", "operations"}


class SkillLayoutTests(unittest.TestCase):
    def test_general_skills_are_flat_and_category_directories_are_absent(self):
        actual_skills = {path.name for path in SKILLS.iterdir() if path.is_dir()}

        self.assertEqual(actual_skills, EXPECTED_SKILLS)
        for skill in EXPECTED_SKILLS:
            self.assertTrue((SKILLS / skill / "SKILL.md").is_file(), skill)
        self.assertTrue(LEGACY_CATEGORY_DIRECTORIES.isdisjoint(actual_skills))


if __name__ == "__main__":
    unittest.main()
