"""Synthetic Tailscale identity regressions; run under the fenced launcher."""
import copy
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/script-manager/scripts'))
import egress_switch
import egress_inspect


def peer(n):
    return {'ID': f'node{n}', 'HostName': f'us-sea-wg-{n}',
            'DNSName': f'us-sea-wg-{n}.mullvad.ts.net.', 'Online': True,
            'ExitNodeOption': True, 'Tags': ['tag:mullvad-exit-node'],
            'TailscaleIPs': [f'100.96.176.{n}/32', f'fd7a:115c:a1e0::{n}/128'],
            'Location': {'Country': 'USA', 'CountryCode': 'US', 'City': 'Seattle, WA'}}


def fixture(n):
    p = peer(n)
    return {'BackendState': 'Running', 'ExitNodeStatus': {'ID': p['ID'], 'Online': True,
            'TailscaleIPs': p['TailscaleIPs']}, 'Peer': {'a': peer(1), 'b': peer(2)}}


def listing(n):
    return '\n'.join(f'100.96.176.{i} us-sea-wg-{i}.mullvad.ts.net USA Seattle, WA '
                     + ('selected' if i == n else '-') for i in (1, 2))


class IdentityTests(unittest.TestCase):
    def test_selection_and_verification_reject_contradictory_exit_hostname(self):
        for n in (1, 2):
            with self.subTest(n=n):
                status = fixture(n)
                status['ExitNodeStatus']['HostName'] = f'us-sea-wg-{3-n}'
                observed = ('tailscale', {'effective_id': f'node{n}'})
                candidate = {'id': 'node2', 'hostname': 'us-sea-wg-2',
                             'city': 'Seattle, WA', 'state': 'WA'}
                def read(*args):
                    return json.dumps(status) if args[1] == 'status' else listing(n)
                with patch.object(egress_switch, 'read', side_effect=read):
                    with self.assertRaises(egress_switch.Invalid):
                        if n == 1:
                            egress_switch.tailscale_selection(observed)
                        else:
                            egress_switch.verify(observed, candidate)

    def test_inspector_rejects_conflicting_peer_evidence(self):
        status = fixture(1)
        status['ExitNodeStatus']['HostName'] = 'us-sea-wg-2'
        replies = {('tailscale', 'get', 'exit-node'): '100.96.176.1',
                   ('tailscale', 'status', '--json'): json.dumps(status),
                   ('tailscale', 'debug', 'prefs'): json.dumps({'RouteAll': False, 'ExitNodeID': 'node1'}),
                   ('mullvad', 'status', '--json'): '{"state":"disconnected"}',
                   ('ip', '-4', 'route', 'get', '1.1.1.1'): '1.1.1.1 dev tailscale0'}
        with patch.object(egress_inspect, 'run', side_effect=lambda *args: ('ok', replies[args])):
            result = egress_inspect.inspect_host()
        self.assertEqual(result['manager'], 'unknown')

    def exercise(self, status, n):
        observed = ('tailscale', {'effective_id': f'node{n}'})
        candidate = {'id': 'node2', 'hostname': 'us-sea-wg-2',
                     'city': 'Seattle, WA', 'state': 'WA'}
        with patch.object(egress_switch, 'read', side_effect=lambda *args:
                          json.dumps(status) if args[1] == 'status' else listing(n)):
            return (egress_switch.tailscale_selection(observed) if n == 1
                    else egress_switch.verify(observed, candidate))

    def test_realistic_and_optional_identity_fields_are_accepted(self):
        for n in (1, 2):
            cases = [fixture(n), fixture(n), fixture(n), fixture(n)]
            cases[1]['ExitNodeStatus'].pop('TailscaleIPs')
            cases[2]['ExitNodeStatus']['TailscaleIPs'] = [f'100.96.176.{n}']
            cases[2]['ExitNodeStatus'].update(HostName=f'US-SEA-WG-{n}',
                                               DNSName=f'US-SEA-WG-{n}.MULLVAD.TS.NET')
            cases[3]['Peer']['unrelated'] = {'ID': 'unrelated', 'TailscaleIPs': 'unsupported'}
            for status in cases:
                with self.subTest(n=n, node=status['ExitNodeStatus']):
                    self.exercise(status, n)

    def test_selection_never_chooses_a_duplicate_candidate_peer(self):
        status = fixture(1)
        status['Peer']['duplicate'] = copy.deepcopy(status['Peer']['b'])
        with self.assertRaises(egress_switch.Invalid):
            self.exercise(status, 1)

    def test_present_conflicting_or_invalid_evidence_is_rejected(self):
        for n in (1, 2):
            cases = []
            for key, value in [('DNSName', f'us-sea-wg-{3-n}.mullvad.ts.net.'),
                               ('TailscaleIPs', [f'100.96.176.{n}', 'fd7a:115c:a1e0::99']),
                               ('TailscaleIPs', ['not-an-ip']), ('HostName', 123)]:
                status = fixture(n); status['ExitNodeStatus'][key] = value; cases.append(status)
            status = fixture(n); status['Peer']['duplicate'] = copy.deepcopy(status['Peer']['a' if n == 1 else 'b']); cases.append(status)
            status = fixture(n); status['Peer']['other'] = {'ID': 'other', 'TailscaleIPs': ['bad', f'100.96.176.{n}']}; cases.append(status)
            status = fixture(n); status['Peer']['a' if n == 1 else 'b']['Online'] = False; cases.append(status)
            status = fixture(n); status['ExitNodeStatus']['ID'] = f'node{3-n}'; cases.append(status)
            status = fixture(n); status['BackendState'] = 'Stopped'; cases.append(status)
            for status in cases:
                with self.subTest(n=n, status=status):
                    with self.assertRaises(egress_switch.Invalid):
                        self.exercise(status, n)

    def test_inspector_accepts_no_peer_enrichment_but_rejects_alias_collision(self):
        status = fixture(1)
        status.pop('Peer')
        self.assertTrue(egress_inspect.exit_identity_consistent(status))
        status['Peer'] = {'other': {'ID': 'other', 'TailscaleIPs': ['100.96.176.1']}}
        self.assertFalse(egress_inspect.exit_identity_consistent(status))
