"""Documentation contract only: never install or access a mailbox."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def check_mail(source):
    text = " ".join(source.split())
    assert "name: mail" in text
    assert "Ordinary inbox access is not restricted to OTPs" in text
    assert text.index("1. Use the active, authenticated Gmail MCP") < text.index("2. Otherwise use **Composio CLI**")
    assert "curl -fsSL https://composio.dev/install | sh" in text
    assert "Never request passwords, tokens, OAuth codes, or callback URLs in chat" in text
    assert "composio execute GMAIL_FETCH_EMAILS --get-schema" in text
    assert "https://docs.composio.dev/docs/cli" in text
    assert "Reading/searching grants no sending" in text


class MailContract(unittest.TestCase):
    def test_contract(self):
        check_mail((ROOT / "skills/mail/SKILL.md").read_text())

    def test_missing_provider_fails(self):
        text = (ROOT / "skills/mail/SKILL.md").read_text()
        token = "2. Otherwise use **Composio CLI**"
        self.assertEqual(text.count(token), 1)
        with self.assertRaises(ValueError):
            check_mail(text.replace(token, "2. Use another provider"))

    def test_routes(self):
        for path in ("README.md", "skills/gmail-otp/SKILL.md"):
            self.assertIn("`mail`", (ROOT / path).read_text())
        self.assertTrue((ROOT / "skills/mail/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
