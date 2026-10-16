"""Documentation contract: BBH registry ownership, legacy non-web isolation."""

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "account-manager"
REGISTRY = "$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json"
LEGACY_NON_WEB = "~/Shared/bounty_recon/{program}/shared/accounts.md"
DEPRECATED_WEB = "~/Shared/web_bounty/{program}/shared/accounts.md"


class AccountManagerRoutingTests(unittest.TestCase):
    def test_main_skill_routes_bbh_to_registry_owner(self):
        text = (SKILL / "SKILL.md").read_text()
        bbh, legacy = text.split("## Legacy non-web programs outside BBH", 1)
        self.assertIn("load BBH's `account-management` skill".lower(), bbh.lower())
        self.assertIn(REGISTRY, bbh)
        self.assertIn("account_inventory.py", bbh)
        self.assertIn("not the authority", bbh)
        self.assertNotIn(DEPRECATED_WEB, text)
        self.assertIn(LEGACY_NON_WEB, legacy)
        self.assertIn("not managed by BBH", legacy)
        self.assertIn("initialize it via `account-management`", legacy)
        self.assertIn("legacy table", legacy)

    def test_reference_cannot_restore_deprecated_web_table(self):
        text = (SKILL / "references/account-table.md").read_text()
        bbh, legacy = text.split("## Legacy non-web path", 1)
        self.assertIn("load `account-management`", bbh)
        self.assertIn(REGISTRY, bbh)
        self.assertIn("account_inventory.py", bbh)
        self.assertNotIn(DEPRECATED_WEB, text)
        self.assertIn(LEGACY_NON_WEB, legacy)
        self.assertIn("non-BBH programs", legacy)
        self.assertIn("must be initialized via `account-management`", legacy)
        self.assertIn("remaining guidance on this page applies only", legacy)


if __name__ == "__main__":
    unittest.main()
