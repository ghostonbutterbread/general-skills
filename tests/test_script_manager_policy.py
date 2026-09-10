import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "script_manager" / "SKILL.md"


class ScriptManagerPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = " ".join(SKILL.read_text(encoding="utf-8").lower().split())

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


if __name__ == "__main__":
    unittest.main()
