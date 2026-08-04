import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "papercut.py"


class PapercutCliTests(unittest.TestCase):
    def run_cli(self, *args, env=None):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def test_add_list_and_close_preserve_history(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            add = self.run_cli(
                "--file", str(record), "add", "--category", "tool",
                "--summary", "Missing helper", "--context", "unit test",
                "--impact", "cost one retry", "--evidence", "fallback worked",
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            identifier = add.stdout.split()[1]
            listed = self.run_cli("--file", str(record), "list")
            self.assertIn(identifier, listed.stdout)
            closed = self.run_cli(
                "--file", str(record), "close", "--id", identifier,
                "--resolution", "Added a fallback",
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertIn(f"- [x] **{identifier}**", record.read_text())
            self.assertIn("Resolution: Added a fallback", record.read_text())
            self.assertIn("no open papercuts", self.run_cli("--file", str(record), "list").stdout)

    def test_rejects_sensitive_material(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            result = self.run_cli(
                "--file", str(record), "add", "--category", "tool",
                "--summary", "Authorization header leaked", "--context", "test",
                "--impact", "unsafe", "--evidence", "none",
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(record.exists())


if __name__ == "__main__":
    unittest.main()
