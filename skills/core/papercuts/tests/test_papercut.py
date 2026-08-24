import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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
                "--evidence", "fallback worked",
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

    def test_uses_shared_record_and_records_source_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ | {"HOME": directory, "PAPERCUTS_SOURCE": "hoster"}
            result = self.run_cli(
                "add", "--category", "tool", "--summary", "Missing helper",
                "--context", "shared record test", env=environment,
            )
            record = Path(directory) / "Shared" / "PAPERCUTS.md"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(record.exists())
            self.assertIn("Source: hoster", record.read_text())

    def test_concurrent_adds_preserve_every_entry_and_use_unique_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"

            def add(index: int):
                return self.run_cli(
                    "--file", str(record), "add", "--category", "tool",
                    "--summary", f"Missing helper {index}", "--context", "concurrent test",
                )

            with ThreadPoolExecutor(max_workers=16) as executor:
                results = list(executor.map(add, range(32)))
            self.assertTrue(all(result.returncode == 0 for result in results), [result.stderr for result in results])
            identifiers = [result.stdout.split()[1] for result in results]
            self.assertEqual(len(set(identifiers)), 32)
            content = record.read_text(encoding="utf-8")
            self.assertEqual(content.count("- [ ] **PC-"), 32)

    def test_accepts_a_record_with_closed_heading_at_end_of_file(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            record.write_text("# Papercuts\n\n## Open\n\n## Closed\n", encoding="utf-8")
            result = self.run_cli("--file", str(record), "list")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no open papercuts", result.stdout)

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
