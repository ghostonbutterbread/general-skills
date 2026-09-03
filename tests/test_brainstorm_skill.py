from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "brainstorm" / "SKILL.md"


class BrainstormSkillTests(unittest.TestCase):
    def test_brainstorm_is_a_general_evidence_grounded_skill(self):
        content = SKILL.read_text()

        self.assertTrue(content.startswith("---\n"))
        self.assertIn("name: brainstorm", content)
        self.assertIn('description: "Explore diverse, evidence-grounded ideas for a problem."', content)
        self.assertIn("It turns a compact evidence or problem packet", content)
        self.assertIn("Any domain can supply the packet", content)
        self.assertIn("The domain workflow\nowns validation, safety, and action.", content)

    def test_seeded_divergence_is_portable_and_uses_a_defined_lens_deck(self):
        content = SKILL.read_text()

        normalized = " ".join(content.split())
        self.assertIn("Keep the first four distinct lens groups encountered", normalized)
        self.assertIn("Append absent groups in the printed deck order", normalized)
        self.assertIn("Use exactly the first four groups after that completion.", normalized)
        self.assertIn("Without a seed, use the first four deck groups in printed order.", normalized)
        self.assertNotIn("`terminal`", content)
        self.assertNotIn("/home/", content)
        self.assertNotIn("localhost", content)
        self.assertIn("The deck controls only lens order and coverage.", content)

    def test_critic_and_discriminator_keep_results_falsifiable(self):
        content = SKILL.read_text()

        self.assertIn("Use a fresh critic.", content)
        self.assertIn("strongest alternative explanation", content)
        self.assertIn("one discriminating question or next observation.", content)
        self.assertIn("a brainstorm can identify a next question; it cannot\n  prove the answer", content)


if __name__ == "__main__":
    unittest.main()
