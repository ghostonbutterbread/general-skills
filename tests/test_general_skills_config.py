from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "general_skills_config.py"


def load_module():
    spec = importlib.util.spec_from_file_location("general_skills_config", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GeneralSkillsConfigTests(unittest.TestCase):
    def test_config_is_generated_without_machine_specific_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            with patch.dict(os.environ, {"GENERAL_SKILLS_CONFIG": str(path)}, clear=False):
                module = load_module()
                self.assertEqual(module.ensure_config(), path)
                contents = path.read_text()

            self.assertIn('identity_file = "~/.ssh/hoster"', contents)
            self.assertIn('central = "~/notes/appsec/faq"', contents)
            self.assertNotIn("/home/ryushe", contents)

    def test_environment_override_wins_over_the_generated_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            with patch.dict(
                os.environ,
                {
                    "GENERAL_SKILLS_CONFIG": str(path),
                    "HOSTER_SSH_KEY": "~/keys/hoster-ed25519",
                },
                clear=False,
            ):
                module = load_module()
                actual = module.configured_path(
                    "hoster", "identity_file", environment="HOSTER_SSH_KEY", default="~/.ssh/hoster"
                )

            self.assertEqual(actual, Path.home() / "keys" / "hoster-ed25519")


if __name__ == "__main__":
    unittest.main()