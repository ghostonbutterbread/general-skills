"""Discovery text must disclose the optional refresh mutation."""
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/script-manager/scripts'


class EgressDiscoveryTests(unittest.TestCase):
    def assert_refresh_disclosure(self, text):
        text = ' '.join(text.lower().split())
        self.assertRegex(text, r'optional refresh[^.]*switch')
        self.assertRegex(text, r'same-manager[^.]*same-city')
        self.assertRegex(text, r'checks[^.]*point-in-time only')
        self.assertIn('continuous', text)
        self.assertNotRegex(text, r'production.gated')

    def test_actual_cli_help_discloses_refresh_mutation(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / 'egress_snapshot.py'), '--help'],
            capture_output=True, text=True, check=True,
        )
        self.assert_refresh_disclosure(result.stdout)

    def test_script_index_discloses_refresh_mutation(self):
        index = (SCRIPTS / 'README.md').read_text()
        entry = next(line for line in index.splitlines()
                     if line.startswith('- `egress_snapshot.py`'))
        self.assert_refresh_disclosure(entry)


if __name__ == '__main__':
    unittest.main()
