from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "account-manager",
    "account-tui-colors",
    "bitwarden",
    "brainstorm",
    "coordination",
    "daddy",
    "evidence-first-vulnerability-reporting",
    "faq",
    "gmail-otp",
    "hoster-ssh",
    "hoster-tmux-child-reaper",
    "i-have-adhd",
    "nightly-learning",
    "papercuts",
    "resilio-sync",
    "safe-fetch",
    "script_manager",
    "security-reporting",
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

    def test_skill_seed_guidance_keeps_capability_boundaries_explicit(self):
        guidance = (SKILLS / "skill-seeds" / "SKILL.md").read_text()

        self.assertIn("Repositories are the top-level capability boundary.", guidance)
        self.assertIn("`general-skills` stays\nflat", guidance)
        self.assertIn("security/BBH capability repository", guidance)
        self.assertIn("flat `mobile-security` repository", guidance)
        self.assertIn("canonical repository and\n  repository-relative path explicitly", guidance)


if __name__ == "__main__":
    unittest.main()
