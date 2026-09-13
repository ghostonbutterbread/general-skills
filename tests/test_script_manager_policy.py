import re
import shutil
import tempfile
import unittest
from pathlib import Path


def validate_owned_links(root: Path) -> None:
    required = {
        "SKILL.md": {"scripts/README.md", "references/script-record-template.md"},
        "scripts/README.md": {"../references/script-record-template.md", "../SKILL.md"},
    }
    for relative, expected in required.items():
        source = root / relative
        text = " ".join(source.read_text(encoding="utf-8").split())
        targets = set(re.findall(r"\]\(([^)]+)\)", text))
        assert expected <= targets, f"Missing pointer in {relative}"
        for target in targets:
            assert (source.parent / target).is_file(), f"Missing reference: {target}"


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

    def test_skill_first_discovery_respects_existing_layout(self) -> None:
        self.assertIn("load the relevant skill first", self.text)
        self.assertIn("read that reference to locate and reuse or edit", self.text)
        self.assertIn("skill-local testing or scripts readme", self.text)
        self.assertIn("`docs/` or `references/`", self.text)
        self.assertIn("do not automatically use the repository-root readme", self.text)
        self.assertIn("or require a global `script_index.md` catalog", self.text)
        self.assertNotIn("$home/.hermes/synced-skills", self.text)

    def test_minimal_records_and_maintenance_boundary(self) -> None:
        self.assertIn("script path plus purpose/when to use it", self.text)
        self.assertIn("new, renamed, or removed scripts must update the same", self.text)
        self.assertIn("skill's pointer as needed", self.text)
        self.assertIn("not installed or synced projections", self.text)
        self.assertIn("adding a pointer to the script map", self.text)
        self.assertIn("main `skill.md` is permitted; no unrelated body edits", self.text)
        self.assertIn("may freely maintain associated script map/index entries", self.text)
        self.assertIn("existing `docs/`, `references/`, or skill-local readme layout", self.text)
        self.assertIn("creating a script must update that map in the same change", self.text)
        self.assertIn("does not authorize other skill or policy changes", self.text)
        self.assertNotIn("obtain that lane owner's authorization", self.text)
        self.assertNotIn("does not override its restriction", self.text)
        for owner in ("coding-policy", "coding-agent-operations-policy", "branch-lifecycle"):
            self.assertIn(f"`{owner}`", self.text)
        template = (SKILL.parent / "references/script-record-template.md").read_text()
        entry = template.split("```md\n", 1)[1].split("```", 1)[0]
        self.assertEqual(entry.strip(), "- `<relative/path/to/script>` — Purpose / when to use it.")

    def test_catalog_is_retained_but_superseded(self) -> None:
        self.assertIn("historical catalog retained", self.index_text)
        self.assertIn("superseded by [script manager]", self.index_text)
        readme = (INDEX.parent / "README.md").read_text()
        self.assertIn("not a required discovery or maintenance step", readme)

    def test_owned_routes_resolve(self) -> None:
        validate_owned_links(SKILL.parent)

    def test_missing_pointer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "script_manager"
            shutil.copytree(SKILL.parent, root)
            source = root / "SKILL.md"
            text = " ".join(source.read_text().split())
            pointer = "[scripts/README.md](scripts/README.md)"
            self.assertEqual(text.count(pointer), 1)
            source.write_text(text.replace(pointer, "script reference"))
            with self.assertRaisesRegex(AssertionError, "Missing pointer"):
                validate_owned_links(root)

    def test_missing_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "script_manager"
            shutil.copytree(SKILL.parent, root)
            (root / "references/script-record-template.md").unlink()
            with self.assertRaisesRegex(AssertionError, "Missing reference"):
                validate_owned_links(root)

    def test_multiple_cohesive_scripts_are_allowed_without_duplication(self) -> None:
        self.assertIn("multiple cohesive scripts", self.text)
        self.assertIn("one giant script", self.text)
        self.assertIn("responsibility already matches", self.text)


if __name__ == "__main__":
    unittest.main()
