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
    "dotfile-management",
    "faq",
    "mail",
    "hoster-ssh",
    "hoster-tmux-child-reaper",
    "atme",
    "i-have-adhd",
    "nightly-learning",
    "papercuts",
    "resilio-sync",
    "safe-fetch",
    "script-manager",
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

    def test_dotfile_management_preserves_actual_application_paths(self):
        skill = (SKILLS / "dotfile-management" / "SKILL.md").read_text()

        self.assertIn("~/.config/kitty/kitty.conf", skill)
        self.assertIn("kitty/.config/kitty/kitty.conf", skill)
        self.assertIn("Use this skill for `ryushe/dotfiles`", skill)
        self.assertIn("./ln_dotfiles.sh", skill)
        self.assertIn("do not create `.ln` files or individual", skill)

    def test_papercut_router_loads_distinct_capture_and_repair_guidance(self):
        root = SKILLS / "papercuts"
        router = (root / "SKILL.md").read_text()
        capture = (root / "references" / "capture.md").read_text()
        repair = (root / "references" / "repair.md").read_text()
        self.assertIn("references/capture.md", router)
        self.assertIn("references/repair.md", router)
        self.assertIn("before adding", router)
        self.assertIn("without patching", router)
        self.assertIn("do not add another", capture)
        self.assertIn("The helper does not deduplicate automatically", capture)
        self.assertIn("no longer affects us", repair)
        self.assertIn("do not patch", repair)
        self.assertIn("leave it open", repair)
        self.assertIn("fresh task branch and isolated worktree", repair)
        self.assertIn("Do not patch directly on the shared integration or stable branch", repair)
        self.assertIn("reuse another papercut's branch", repair)
        self.assertIn("An evidence-based closure with no patch does not need a code branch", repair)
        self.assertNotIn("--id <", repair)
        self.assertIn("leave the stock installation unchanged", repair)
        self.assertIn("maintenance cost is explained", repair)

    def test_bitwarden_skill_reminds_before_cli_use(self):
        skill = (SKILLS / "bitwarden" / "SKILL.md").read_text()
        description = skill.split("---", 2)[1]
        self.assertIn("Before running the Bitwarden CLI (`bw`), load this skill for its unlock instructions.", description)
        self.assertIn("Before running `bw`, load this skill for its unlock instructions.", skill)

    def test_skill_seed_guidance_keeps_capability_boundaries_explicit(self):
        guidance = (SKILLS / "skill-seeds" / "SKILL.md").read_text()

        self.assertIn("Repositories are the top-level capability boundary.", guidance)
        self.assertIn("`general-skills` stays\nflat", guidance)
        self.assertIn("security/BBH capability repository", guidance)
        self.assertIn("flat `mobile-security` repository", guidance)
        self.assertIn("canonical repository and\n  repository-relative path explicitly", guidance)


if __name__ == "__main__":
    unittest.main()
