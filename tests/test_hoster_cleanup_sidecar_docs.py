from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HosterCleanupSidecarDocsTests(unittest.TestCase):
    def test_sidecar_contract_keeps_main_task_and_cleanup_separate(self):
        reaper = (ROOT / "skills/hoster-tmux-child-reaper/SKILL.md").read_text()
        hoster = (ROOT / "skills/hoster-ssh/SKILL.md").read_text()

        self.assertIn("short-lived\ncleanup sidecar", reaper)
        self.assertIn("while the parent begins", reaper)
        self.assertIn("immediately proceeds with its own task", reaper)
        self.assertIn("The sidecar is an agent role, not a tmux child pane", reaper)
        self.assertIn("cleanup: success | needs-attention | failed", reaper)
        self.assertIn("start a short-lived native cleanup sidecar", hoster)
        self.assertIn("should not wait for a\nroutine receipt before starting", hoster)

    def test_sidecar_contract_preserves_fail_closed_reaper_boundaries(self):
        reaper = (ROOT / "skills/hoster-tmux-child-reaper/SKILL.md").read_text()

        self.assertIn("scope contains **no processes at all**", reaper)
        self.assertIn("Do not manually act on ineligible scopes", reaper)
        self.assertIn("Do not schedule cleanup as a timer, cron job, or unattended loop", reaper)
        self.assertIn("Do not have the cleanup sidecar retrospectively claim arbitrary active scopes", reaper)


if __name__ == "__main__":
    unittest.main()
