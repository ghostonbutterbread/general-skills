import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "papercut.py"


class PapercutCliTests(unittest.TestCase):
    def cli(self, *args, env=None):
        return subprocess.run(["python3", str(SCRIPT), *args], text=True,
                              capture_output=True, check=False, env=env)

    def add(self, record, incident="run-1", severity="low", breaking="no", minutes=2):
        return self.cli("--file", str(record), "add", "--category", "tool",
                        "--summary", "Missing helper", "--context", "unit test",
                        "--severity", severity, "--breaking", breaking,
                        "--reason", "Fallback took time", "--minutes-lost", str(minutes),
                        "--incident", incident)

    def observe(self, record, identifier, incident, minutes=2, *extra):
        return self.cli("--file", str(record), "observe", "--id", identifier,
                        "--incident", incident, "--minutes-lost", str(minutes), *extra)

    def test_e2e_capture_escalate_and_close(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            added = self.add(record)
            self.assertEqual(added.returncode, 0, added.stderr)
            identifier = added.stdout.split()[1]
            self.assertEqual(self.add(record, "other-run", "high", "yes", 30).returncode, 0)
            for n in (2, 3, 4, 5):
                observed = self.observe(record, identifier, f"run-{n}", 20)
                self.assertEqual(observed.returncode, 0, observed.stderr)
            content = record.read_text()
            self.assertIn("Severity: high (agent: low)", content)
            self.assertIn("Occurrences: 5", content)
            self.assertIn("Time lost: 82 min (observed)", content)
            self.assertIn("Escalation: 5 distinct incidents and at least 60 minutes lost", content)
            self.assertEqual(content.count("- [ ] **PC-"), 2)
            self.assertIn(identifier, self.cli("--file", str(record), "list").stdout)
            self.assertIn("unchanged", self.observe(record, identifier, "run-5", 99).stdout)
            self.assertEqual(record.read_text(), content)
            closed = self.cli("--file", str(record), "close", "--id", identifier,
                              "--resolution", "Added a fallback")
            self.assertEqual(closed.returncode, 0, closed.stderr)
            self.assertIn(f"- [x] **{identifier}**", record.read_text())
            self.assertNotIn(identifier, self.cli("--file", str(record), "list").stdout)
            self.assertNotEqual(self.observe(record, identifier, "run-6").returncode, 0)

    def test_frequency_and_critical_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            self.assertNotEqual(self.add(record, severity="critical").returncode, 0)
            self.assertFalse(record.exists())
            identifier = self.add(record, minutes=0).stdout.split()[1]
            for n in range(2, 12):
                self.assertEqual(self.observe(record, identifier, f"run-{n}", 0).returncode, 0)
            self.assertIn("Severity: medium (agent: low)", record.read_text())
            self.assertNotIn("critical", record.read_text())
            blocked = self.add(record, "blocked-1", breaking="yes", minutes=0).stdout.split()[1]
            for n in range(2, 6):
                self.assertEqual(self.observe(record, blocked, f"blocked-{n}", 0).returncode, 0)
            self.assertIn("Severity: high (agent: low)", record.read_text())

    def test_legacy_entry_first_rating_without_invented_history(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            identifier = "PC-20200101-000000-old"
            record.write_text(f"# Papercuts\n\n## Open\n\n- [ ] **{identifier}** [tool] Old issue\n  - Context: test\n\n## Closed\n")
            self.assertIn(identifier, self.cli("--file", str(record), "list").stdout)
            self.assertNotEqual(self.observe(record, identifier, "run-1").returncode, 0)
            rated = self.observe(record, identifier, "run-1", 5, "--severity", "low",
                                 "--breaking", "no", "--reason", "Fallback took time")
            self.assertEqual(rated.returncode, 0, rated.stderr)
            self.assertIn("Occurrences: 1", record.read_text())
            self.assertIn("Time lost: 5 min (observed)", record.read_text())

    def test_agent_raise_supersedes_stale_automatic_escalation(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            identifier = self.add(record).stdout.split()[1]
            for n in (2, 3):
                self.assertEqual(self.observe(record, identifier, f"run-{n}").returncode, 0)
            self.assertIn("Escalation: 3 distinct incidents", record.read_text())
            raised = self.observe(record, identifier, "run-4", 2, "--severity", "high",
                                  "--breaking", "yes", "--reason", "Workflow now blocked")
            self.assertEqual(raised.returncode, 0, raised.stderr)
            self.assertIn("Severity: high (agent: high)", record.read_text())
            self.assertNotIn("Escalation:", record.read_text())
            critical = self.observe(record, identifier, "run-5", 2, "--severity", "critical",
                                    "--reason", "Essential workflow now blocked broadly")
            self.assertEqual(critical.returncode, 0, critical.stderr)
            self.assertIn("Severity: critical (agent: critical)", record.read_text())
            self.assertNotIn("Escalation:", record.read_text())

    def test_duplicate_and_bad_input_do_not_mutate_record(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "PAPERCUTS.md"
            self.assertNotEqual(self.add(record, "run/1").returncode, 0)
            self.assertFalse(record.exists())
            self.assertEqual(self.add(record).returncode, 0)
            before = record.read_text()
            identifier = before.split("**")[1]
            self.assertIn("unchanged", self.observe(record, identifier, "run-1").stdout)
            self.assertEqual(before, record.read_text())
            # One task may encounter two different issues; incident identity is per entry.
            self.assertEqual(self.add(record, "run-1").returncode, 0)
            before = record.read_text()
            self.assertNotEqual(self.observe(record, identifier, "run-2", -1).returncode, 0)
            self.assertEqual(before, record.read_text())
            self.assertEqual(self.cli("--file", str(record), "add", "--category", "tool",
                                      "--summary", "Authorization header leaked", "--context", "test",
                                      "--severity", "low", "--breaking", "no", "--reason", "unsafe",
                                      "--minutes-lost", "0", "--incident", "run-2").returncode, 2)
            self.assertEqual(before, record.read_text())

    def test_shared_default_concurrent_observations_and_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ | {"HOME": directory, "PAPERCUTS_SOURCE": "hoster"}
            result = self.cli("add", "--category", "tool", "--summary", "Missing helper",
                              "--context", "shared test", "--severity", "low", "--breaking", "no",
                              "--reason", "fallback took time", "--minutes-lost", "1",
                              "--incident", "run-1", env=env)
            record = Path(directory) / "Shared" / "PAPERCUTS.md"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Source: hoster", record.read_text())
            identifier = result.stdout.split()[1]
            with ThreadPoolExecutor(max_workers=12) as executor:
                results = list(executor.map(lambda n: self.observe(record, identifier, f"run-{n}", 1), range(2, 22)))
            self.assertTrue(all(r.returncode == 0 for r in results), [r.stderr for r in results])
            self.assertIn("Occurrences: 21", record.read_text())
            self.assertIn("Time lost: 21 min (observed)", record.read_text())
            empty = Path(directory) / "empty.md"
            empty.write_text("# Papercuts\n\n## Open\n\n## Closed\n")
            self.assertIn("no open papercuts", self.cli("--file", str(empty), "list").stdout)


if __name__ == "__main__":
    unittest.main()
