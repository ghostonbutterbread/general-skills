"""Path-only checks; never execute Bitwarden scripts or CLI."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/bitwarden"
INIT = 'BITWARDEN_SKILL_DIR="${BITWARDEN_SKILL_DIR:-$HOME/.hermes/synced-skills/bitwarden}"'


class BitwardenSkillPathTests(unittest.TestCase):
    def test_guidance_uses_one_skill_directory_for_both_scripts(self):
        main = (SKILL / "SKILL.md").read_text()
        account_storage = (SKILL / "references/account-storage.md").read_text()
        self.assertEqual(main.count(INIT), 2)
        self.assertIn(INIT, account_storage)
        for text in (main, account_storage):
            self.assertIn('source "$BITWARDEN_SKILL_DIR/scripts/bw-session.sh"', text)
            self.assertNotIn('source skills/bitwarden/scripts/bw-session.sh', text)
        self.assertIn('"$BITWARDEN_SKILL_DIR/scripts/bw-create-login.sh"', main)
        self.assertNotIn('   skills/bitwarden/scripts/bw-create-login.sh', main)

    def test_documented_resolution_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            installed = home / ".hermes/synced-skills/bitwarden"
            installed.parent.mkdir(parents=True)
            installed.symlink_to(SKILL, target_is_directory=True)
            unrelated_cwd = root / "bbh"
            unrelated_cwd.mkdir()
            for override in (None, str(SKILL)):
                env = {**os.environ, "HOME": str(home)}
                env.pop("BITWARDEN_SKILL_DIR", None)
                if override is not None:
                    env["BITWARDEN_SKILL_DIR"] = override
                script = (INIT + '\n'
                          'test -f "$BITWARDEN_SKILL_DIR/scripts/bw-session.sh" && '
                          'test -x "$BITWARDEN_SKILL_DIR/scripts/bw-create-login.sh"')
                subprocess.run(["bash", "-c", script], cwd=unrelated_cwd,
                               env=env, check=True)


if __name__ == "__main__":
    unittest.main()
