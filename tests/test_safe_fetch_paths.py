from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "safe-fetch" / "scripts" / "safe_fetch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("safe_fetch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SafeFetchPathTests(unittest.TestCase):
    def test_quarantine_override_is_an_exact_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            expected = Path(temporary) / "quarantine"
            with patch.dict(os.environ, {"SAFE_FETCH_QUARANTINE": str(expected)}, clear=False):
                module = load_module()

            self.assertEqual(module.DEFAULT_QUARANTINE, expected)


if __name__ == "__main__":
    unittest.main()
