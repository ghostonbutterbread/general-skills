"""CLI regressions adapted from shared-egress-recovery's inspect fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/script-manager/scripts/egress_inspect.py'


class InspectTests(unittest.TestCase):
    def setUp(self):
        if not os.environ.get('TMPDIR'):
            self.skipTest('set TMPDIR to a private scratch directory for offline fixtures')
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = {'HOME': str(self.root), 'TMPDIR': str(self.root), 'PATH': str(self.bin),
                    'XDG_CONFIG_HOME': str(self.root / 'config'), 'XDG_STATE_HOME': str(self.root / 'state'),
                    'XDG_CACHE_HOME': str(self.root / 'cache'), 'PYTHONDONTWRITEBYTECODE': '1',
                    'LC_ALL': 'C.UTF-8', 'FIXTURE': str(self.root)}

    def fake_tools(self, replies):
        (self.root / 'replies.json').write_text(json.dumps(replies))
        source = f'''#!{sys.executable}
import json, os, sys, time
root = os.environ['FIXTURE']
key = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
with open(root + '/calls', 'a') as f: f.write(key + '\\n')
reply = json.load(open(root + '/replies.json'))[key]
if reply[1] == '<timeout>': time.sleep(10)
if reply[1] == '<invalid-utf8>': sys.stdout.buffer.write(bytes([255])); sys.exit(reply[0])
sys.stdout.write(reply[1]); sys.exit(reply[0])
'''
        for name in ('tailscale', 'mullvad', 'ip'):
            p = self.bin / name
            p.unlink(missing_ok=True)
            if any(k.startswith(name + ' ') for k in replies):
                p.write_text(source)
                p.chmod(0o700)

    def inspect(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def observed(self):
        return {
            'tailscale get exit-node': [0, '100.96.176.46\n'],
            'tailscale status --json': [0, json.dumps({'BackendState': 'Running',
                'ExitNodeStatus': {'ID': 'node1', 'Online': True, 'TailscaleIPs': ['100.96.176.46/32']}})],
            'tailscale debug prefs': [0, json.dumps({'RouteAll': False, 'ExitNodeID': 'node1'})],
            'mullvad status --json': [0, json.dumps({'state': 'disconnected', 'details': {'location': {'mullvad_exit_ip': True}}})],
            'ip -4 route get 1.1.1.1': [0, '1.1.1.1 dev tailscale0 table 52\n'],
        }

    def test_observed_tailscale_routeall_false_and_disconnected_mullvad(self):
        self.fake_tools(self.observed())
        receipt = self.inspect()
        self.assertEqual(receipt['manager'], 'tailscale')
        self.assertEqual(receipt['tailscale']['selected'], 'selected')
        self.assertEqual(receipt['tailscale']['effective'], 'online')
        self.assertEqual(receipt['tailscale']['route_all'], False)
        self.assertEqual(receipt['mullvad']['state'], 'disconnected')
        self.assertEqual(receipt['route']['interface'], 'tailscale0')
        self.assertEqual(receipt['action'], 'none')
        self.assertIs(receipt['exhaustive'], False)
        self.assertEqual(set((self.root / 'calls').read_text().splitlines()), set(self.observed()))
        self.assertFalse((self.root / 'state').exists())

    def test_standalone_connection_is_inferred_only_with_matching_observations(self):
        replies = self.observed()
        replies['tailscale get exit-node'] = [0, '']
        replies['tailscale status --json'] = [0, json.dumps({'BackendState': 'Running'})]
        replies['tailscale debug prefs'] = [0, json.dumps({'RouteAll': False, 'ExitNodeID': ''})]
        replies['mullvad status --json'] = [0, json.dumps({'state': 'connected'})]
        replies['ip -4 route get 1.1.1.1'] = [0, '1.1.1.1 dev wg-mullvad']
        self.fake_tools(replies)
        result = self.inspect()
        self.assertEqual(result['manager'], 'mullvad')
        self.assertEqual(result['tailscale']['effective'], 'none')
        self.assertEqual(result['mullvad']['state'], 'connected')

    def test_unavailable_commands_are_unknown_not_system_wide_absence(self):
        self.fake_tools({'ip -4 route get 1.1.1.1': [0, '1.1.1.1 dev eth0']})
        result = self.inspect()
        self.assertEqual(result['manager'], 'unknown')
        self.assertEqual(result['tailscale']['selected'], 'unknown')
        self.assertEqual(result['tailscale']['effective'], 'unknown')
        self.assertEqual(result['mullvad']['state'], 'unknown')
        self.assertIn('mullvad-status-not-on-path', result['issues'])

    def test_invalid_conflicting_and_unavailable_evidence(self):
        cases = [
            ('tailnet alone', {'tailscale status --json': [0, '{"BackendState":"Running"}']}, 'tailscale-selection-mismatch'),
            ('selection mismatch', {'tailscale get exit-node': [0, '100.96.176.47']}, 'tailscale-selection-mismatch'),
            ('offline', {'tailscale status --json': [0, '{"BackendState":"Running","ExitNodeStatus":{"ID":"node1","Online":false}}']}, 'tailscale-exit-offline'),
            ('conflicting manager', {'mullvad status --json': [0, '{"state":"connected"}']}, 'manager-conflict'),
            ('malformed status', {'tailscale status --json': [0, 'not json']}, 'tailscale-status-invalid'),
            ('failed status', {'tailscale status --json': [1, '']}, 'tailscale-status-failed'),
            ('bad encoding', {'mullvad status --json': [0, '<invalid-utf8>']}, 'mullvad-status-failed'),
            ('transition', {'mullvad status --json': [0, '{"state":"connecting"}']}, 'mullvad-status-unknown'),
            ('prefs mismatch', {'tailscale debug prefs': [0, '{"RouteAll":false,"ExitNodeID":"other"}']}, 'tailscale-prefs-mismatch'),
            ('prefs malformed', {'tailscale debug prefs': [0, '{"RouteAll":"false","ExitNodeID":"node1"}']}, 'tailscale-prefs-invalid'),
            ('route mismatch', {'ip -4 route get 1.1.1.1': [0, '1.1.1.1 dev eth0']}, 'ipv4-route-conflict'),
            ('route ambiguous', {'ip -4 route get 1.1.1.1': [0, '1.1.1.1 dev eth0 dev tailscale0']}, 'ipv4-route-invalid'),
            ('route invalid', {'ip -4 route get 1.1.1.1': [0, 'unreachable']}, 'ipv4-route-invalid'),
            ('route failed', {'ip -4 route get 1.1.1.1': [1, '']}, 'ipv4-route-failed'),
            ('invalid mullvad JSON object', {'mullvad status --json': [0, '{}']}, 'mullvad-status-unknown'),
        ]
        for label, override, issue in cases:
            with self.subTest(label=label):
                self.fake_tools(self.observed() | override)
                receipt = self.inspect()
                self.assertEqual(receipt['manager'], 'unknown')
                self.assertIn(issue, receipt['issues'])
                self.assertEqual(receipt['action'], 'none')

    def test_timeout_and_nonexecutable_cli_are_unknown(self):
        replies = self.observed()
        replies['mullvad status --json'] = [0, '<timeout>']
        self.fake_tools(replies)
        result = self.inspect()
        self.assertEqual(result['manager'], 'unknown')
        self.assertIn('mullvad-status-failed', result['issues'])
        self.fake_tools(self.observed())
        (self.bin / 'mullvad').chmod(0o600)
        result = self.inspect()
        self.assertEqual(result['mullvad']['state'], 'unknown')
        self.assertIn('mullvad-status-failed', result['issues'])

    def test_unknown_destination_and_ambiguous_ip_route_are_not_accepted(self):
        for route in ('bogus dev tailscale0', '127.0.0.1 dev tailscale0'):
            with self.subTest(route=route):
                self.fake_tools(self.observed() | {'ip -4 route get 1.1.1.1': [0, route]})
                result = self.inspect()
                self.assertEqual(result['manager'], 'unknown')
                self.assertIn('ipv4-route-invalid', result['issues'])


if __name__ == '__main__':
    unittest.main()
