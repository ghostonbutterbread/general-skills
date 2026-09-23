"""Offline mail routing/setup checks; never install or read a mailbox."""
from pathlib import Path
import tempfile
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIL = ROOT / "skills/mail"


def check_mail(owner):
    hot = " ".join((owner / "SKILL.md").read_text().split())
    setup = (owner / "references/setup.md").read_text()
    assert "name: mail" in hot
    assert "Use **Composio CLI**" in hot
    assert "references/setup.md" in hot
    assert "Gmail" not in hot and "@" not in hot
    assert "gmail-otp" not in hot
    assert "curl" not in hot
    assert "Never request passwords, tokens, OAuth codes, or callback URLs in chat" in hot
    assert "curl -fsSL https://composio.dev/install | sh" in setup
    assert "composio execute GMAIL_FETCH_EMAILS --get-schema" in setup
    assert "https://docs.composio.dev/docs/cli" in setup


class MailContract(unittest.TestCase):
    def test_contract(self):
        check_mail(MAIL)

    def test_missing_setup_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            owner = Path(temp) / "mail"
            shutil.copytree(MAIL, owner)
            (owner / "references/setup.md").unlink()
            with self.assertRaises(FileNotFoundError):
                check_mail(owner)

    def test_missing_route_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            owner = Path(temp) / "mail"
            shutil.copytree(MAIL, owner)
            path = owner / "SKILL.md"
            text = path.read_text()
            self.assertEqual(text.count("references/setup.md"), 1)
            path.write_text(text.replace("references/setup.md", "elsewhere.md"))
            with self.assertRaises(AssertionError):
                check_mail(owner)

    def test_shared_catalog_uses_mail_not_legacy_wrapper(self):
        self.assertIn("`mail`", (ROOT / "README.md").read_text())
        self.assertFalse((ROOT / "skills/gmail-otp").exists())


if __name__ == "__main__":
    unittest.main()
