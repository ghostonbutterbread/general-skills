import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "script_manager" / "SKILL.md"
INDEX = Path(__file__).resolve().parents[1] / "SCRIPT_INDEX.md"


class ScriptManagerPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = " ".join(SKILL.read_text(encoding="utf-8").lower().split())
        cls.index_text = " ".join(INDEX.read_text(encoding="utf-8").lower().split())

    def test_deterministic_scripts_have_bounded_authority(self) -> None:
        self.assertIn("deterministic mechanics, bounded authority", self.text)
        self.assertIn("exhaustive: false", self.text)
        self.assertIn("zero matches", self.text)
        self.assertIn("observed facts", self.text)
        self.assertIn("seed signals", self.text)
        self.assertIn("unknowns", self.text)

    def test_script_learning_requires_evidence_and_review(self) -> None:
        self.assertIn("preserved triggering evidence", self.text)
        self.assertIn("failing fixture or test", self.text)
        self.assertIn("generalized implementation", self.text)
        self.assertIn("validation against false positives, and review", self.text)

    def test_repository_policy_is_discovered_without_repo_specific_wording(self) -> None:
        self.assertIn("script_policy.md", self.text)
        self.assertIn("root of the repository you are working in", self.text)
        self.assertIn("storage, indexing, and maintenance conventions", self.text)
        self.assertIn("supersedes these generic defaults", self.text)
        self.assertIn("cannot override higher-priority safety", self.text)
        self.assertNotIn("selected bbh checkout", self.text)
        self.assertNotIn("bug bounty skill helper", self.text)

    def test_general_index_is_repository_neutral(self) -> None:
        self.assertIn("general skills source index", self.index_text)
        self.assertIn("script_policy.md", self.index_text)
        self.assertNotIn("bug_bounty_harness", self.index_text)
        self.assertNotIn("bounty_recon", self.index_text)
        self.assertNotIn(".openclaw/workspace", self.index_text)

    def test_multiple_cohesive_scripts_are_allowed_without_duplication(self) -> None:
        self.assertIn("multiple cohesive scripts", self.text)
        self.assertIn("one giant script", self.text)
        self.assertIn("responsibility already matches", self.text)


if __name__ == "__main__":
    unittest.main()
