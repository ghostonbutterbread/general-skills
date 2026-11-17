"""Documentation contract for controller lookup, not provider tests."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/my-computer/SKILL.md"


class MyComputerSkillTests(unittest.TestCase):
    def text(self):
        self.assertTrue(SKILL.is_file(), "the discoverable skill is missing")
        return SKILL.read_text()

    def test_discovery_and_scope(self):
        text = self.text()
        frontmatter = text.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: my-computer$")
        self.assertRegex(frontmatter, r"(?m)^description: .*my computer.*my PC")
        self.assertIn("`my-computer`", (ROOT / "README.md").read_text())
        self.assertIn("my computer", text)
        self.assertIn("my proxy", text)
        self.assertIn("my notes", text)
        self.assertIn("normal meaning", text)

    def test_lookup_is_actionable_on_compatible_installations(self):
        text = self.text()
        normalized = " ".join(text.split())
        for phrase in ("per-pane", "current controller", "inferred", "not proof",
                       "`herdr pane controller --current --json`",
                       "compatible client and server", "current Herdr pane",
                       "without an external verification receipt", "`HERDR_ENV=1`",
                       "Herdr client on that machine's PATH", "stock older or unknown",
                       "do not install, replace, restart, or upgrade a server"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, normalized)
        self.assertRegex(normalized, r"(?i)attempt .*`herdr pane controller --current --json`")
        self.assertIn("verified in an isolated Hoster trial", normalized)
        self.assertIn("Ryushe confirmed actual use", normalized)
        self.assertNotIn("pending provider verification", normalized)
        self.assertNotIn("not a verified deployed interface", normalized)
        self.assertRegex(text, r"(?is)unknown.*ambiguous.*unsupported.*ask Ryushe")
        self.assertIn("`SSH_CONNECTION`", text)
        self.assertIn("stale", text)
        self.assertIn("tmux", text)
        self.assertIn("no verified source mechanism", text)
        self.assertIn("fresh lookup", text)
        self.assertRegex(text, r"`result.status`\s+is `inferred`")

    def test_nested_result_and_untrusted_hint_are_documented(self):
        text = self.text()
        for phrase in ("`result.type`", "`pane_controller`", "`result.status`",
                       "`result.source_ip`", "`result.reason`",
                       "valid JSON object", "command exits zero", "no error envelope", "valid usable IP",
                       "for the connection", "local Unix-socket peer's", "environment",
                       "untrusted hint", "can be spoofed", "not an authenticated",
                       "network peer"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertRegex(text, r"(?is)missing or malformed response or IP.*unexpected result type.*non-inferred status.*ask Ryushe")

    def test_readme_states_trial_and_compatibility_boundary(self):
        readme = (ROOT / "README.md").read_text()
        entry = next(line for line in readme.splitlines() if line.startswith("- `my-computer`"))
        self.assertRegex(entry, r"verified.*trial.*compatible client and server.*ask")
        self.assertNotIn("Herdr integration is pending verification", entry)

    def test_named_device_uses_existing_host_resolution(self):
        text = self.text()
        for phrase in ("my PC", "Nebula", "explicitly named device", "`getent hosts",
                       "hosts file", "takes precedence"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_proxy_route_preserves_default_and_checks_specific_device_requests(self):
        text = self.text()
        self.assertIn("does not redefine the known", text)
        self.assertIn("named or", text)
        self.assertIn("verify its location and port", text)
        self.assertIn("ask if those are not established", text)

    def test_ip_and_proxy_boundaries(self):
        text = self.text()
        for phrase in ("SSH source IP", "without maintaining a device table", "`/etc/hosts`",
                       "explicitly requests a named host addition", "safe",
                       "`ryushe-proxy`", "`proxy-routing-policy`", "read-only",
                       "task-scoped", "Abommie", "not authorization"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
