"""Documentation contract: BBH registry ownership, legacy non-web isolation."""

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "account-manager"
BITWARDEN = SKILL.parent / "bitwarden"
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

    def test_required_bitwarden_reference_routes_bbh_to_registry(self):
        entry = (BITWARDEN / "SKILL.md").read_text()
        self.assertIn("Read `references/account-storage.md`", entry)
        self.assertIn("follow the lifecycle rules in `references/account-storage.md`", entry)

        reference = (BITWARDEN / "references/account-storage.md").read_text()
        bbh, legacy = reference.split("## Legacy account notes outside BBH", 1)
        self.assertIn("load `account-management`", bbh)
        self.assertIn(REGISTRY, bbh)
        self.assertIn("account_inventory.py", bbh)
        self.assertIn("missing registry", bbh)
        self.assertIn("Do not create or update a parallel account/resource table", bbh)
        self.assertIn("record the non-secret lifecycle/credential-reference", bbh)
        self.assertNotIn(DEPRECATED_WEB, reference)
        self.assertIn("only to non-BBH", legacy)
        self.assertIn("For non-BBH programs only", legacy)
        self.assertIn("Update the target account/resource table", legacy)
        self.assertIn("legacy account/resource table", legacy)
        self.assertIn("For BBH, use `account-management`", legacy)


if __name__ == "__main__":
    unittest.main()
