"""Host-direct snapshot CLI tests; run only under an inherited network fence."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/script-manager/scripts/egress_snapshot.py'


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = {'PATH': str(self.bin), 'HOME': str(self.root), 'TMPDIR': str(self.root),
                    'XDG_STATE_HOME': str(self.root / 'state'), 'XDG_CONFIG_HOME': str(self.root / 'config'),
                    'XDG_CACHE_HOME': str(self.root / 'cache'), 'FIXTURE': str(self.root),
                    'PYTHONDONTWRITEBYTECODE': '1', 'http_proxy': 'http://bad',
                    'HTTPS_PROXY': 'http://bad', 'SSL_CERT_FILE': '/bad'}
        self.replies = {
            'tailscale get exit-node': '100.96.176.46',
            'tailscale status --json': json.dumps({'BackendState': 'Running', 'ExitNodeStatus': {'ID': 'node1', 'Online': True, 'TailscaleIPs': ['100.96.176.46/32']}}),
            'tailscale debug prefs': json.dumps({'RouteAll': False, 'ExitNodeID': 'node1'}),
            'mullvad status --json': json.dumps({'state': 'disconnected'}),
            'ip -4 route get 1.1.1.1': '1.1.1.1 dev tailscale0 table 52',
        }
        self.setup_tools()

    def setup_tools(self):
        (self.root / 'replies.json').write_text(json.dumps(self.replies))
        source = f'''#!{sys.executable} -s
import json, os, sys
root = {str(self.root)!r}
key = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
with open(root + '/calls', 'a') as f: f.write(key + '\\n')
if os.path.basename(sys.argv[0]) == 'curl':
    with open(root + '/curl-env', 'w') as f: json.dump(dict(os.environ), f)
    if os.path.exists(root + '/curl-fail'): sys.exit(22)
    print(open(root + '/response').read(), end='')
    if os.path.exists(root + '/drift.json'):
        os.replace(root + '/drift.json', root + '/replies.json')
else:
    print(json.load(open(root + '/replies.json'))[key])
'''
        for name in ('tailscale', 'mullvad', 'ip', 'curl'):
            p = self.bin / name
            p.write_text(source)
            p.chmod(0o700)
        (self.root / 'response').write_text('fl=1\nip=8.8.8.8\n')

    def run_cli(self, mode, key='incident-1'):
        command = ([sys.executable, str(SCRIPT), mode, key] if mode != 'refresh' else
                   [sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
                    str(self.root), 'production', mode, key])
        return subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=30)

    def test_incident_record_check_and_refresh_without_unnecessary_mutation(self):
        record = self.run_cli('record')
        self.assertEqual(record.returncode, 0, record.stdout + record.stderr)
        self.assertEqual(json.loads(record.stdout)['result'], 'captured')
        # Independent work need not hold a lease or lock.
        (self.root / 'investigation').write_text('continued')
        self.assertEqual(json.loads(self.run_cli('check').stdout)['result'], 'same')
        blocked = self.run_cli('refresh')
        self.assertEqual(json.loads(blocked.stdout)['result'], 'unknown')
        self.assertEqual(json.loads(blocked.stdout)['action'], 'none')
        (self.root / 'response').write_text('ip=9.9.9.9\n')
        changed = self.run_cli('refresh')
        self.assertEqual(changed.returncode, 0, changed.stdout + changed.stderr)
        self.assertEqual(json.loads(changed.stdout)['result'], 'already_refreshed')
        self.assertEqual(json.loads(changed.stdout)['action'], 'none')
        self.assertNotIn('8.8.8.8', record.stdout + changed.stdout + changed.stderr)
        self.assertNotIn('9.9.9.9', record.stdout + changed.stdout + changed.stderr)
        calls = (self.root / 'calls').read_text()
        self.assertNotIn('tailscale set ', calls)
        self.assertNotIn('mullvad disconnect', calls)
        self.assertNotIn('mullvad reconnect', calls)

    def test_record_failure_persists_unknown_without_later_resampling(self):
        (self.root / 'curl-fail').touch()
        recorded = self.run_cli('record')
        receipt = json.loads(recorded.stdout)
        self.assertEqual(receipt['result'], 'incident_recorded_baseline_unknown')
        self.assertIn('curl failed', receipt['reason'])
        (self.root / 'curl-fail').unlink()
        calls = (self.root / 'calls').read_text()
        for mode in ('record', 'check', 'refresh', 'capture', 'compare'):
            result = self.run_cli(mode)
            self.assertEqual(json.loads(result.stdout)['result'], 'unknown', mode)
            self.assertEqual((self.root / 'calls').read_text(), calls, mode)
        self.assertNotIn('8.8.8.8', recorded.stdout + recorded.stderr)

    def fixture_cli(self, kind, mode, key):
        return subprocess.run([sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
                               str(self.root), kind, mode, key], env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_first_use_peer_syncs_parent_when_creator_dies_before_sync(self):
        import select
        ready_read, ready_write = os.pipe()
        release_read, release_write = os.pipe()
        env = dict(self.env, READY_FD=str(ready_write), RELEASE_FD=str(release_read))
        cmd = [sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
               str(self.root), 'mkdir-pause', 'record', 'creator']
        creator = subprocess.Popen(cmd, env=env, pass_fds=(ready_write, release_read),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        os.close(ready_write)
        os.close(release_read)
        try:
            self.assertTrue(select.select([ready_read], [], [], 15)[0], 'creator did not pause')
            self.assertEqual(os.read(ready_read, 1), b'R')
            peer = self.fixture_cli('sync-audit', 'record', 'peer')
            self.assertEqual(json.loads(peer.stdout)['result'], 'captured', peer.stderr)
            synced = (self.root / 'sync-audit').read_text().splitlines()
            self.assertIn(str(self.root), synced, 'peer did not sync the state directory parent')
            self.assertIsNone(creator.poll(), 'creator was not held at the unsynced boundary')
        finally:
            creator.kill()
            creator.communicate(timeout=15)
            os.close(ready_read)
            os.close(release_write)

    def test_symlink_alias_peer_refuses_before_publication_while_creator_paused(self):
        import select
        physical_parent = self.root / 'physical-parent'
        physical_parent.mkdir()
        physical_state = physical_parent / 'new-state'
        alias = self.root / 'alias'
        alias.symlink_to(physical_state, target_is_directory=True)
        ready_read, ready_write = os.pipe()
        release_read, release_write = os.pipe()
        env = dict(self.env, XDG_STATE_HOME=str(physical_state),
                   READY_FD=str(ready_write), RELEASE_FD=str(release_read))
        cmd = [sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
               str(self.root), 'mkdir-pause', 'record', 'creator']
        creator = subprocess.Popen(cmd, env=env, pass_fds=(ready_write, release_read),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        os.close(ready_write)
        os.close(release_read)
        try:
            self.assertTrue(select.select([ready_read], [], [], 15)[0], 'creator did not pause')
            self.assertEqual(os.read(ready_read, 1), b'R')
            self.env['XDG_STATE_HOME'] = str(alias)
            peer = self.fixture_cli('sync-audit', 'record', 'alias-peer')
            self.assertEqual(peer.returncode, 1, peer.stdout + peer.stderr)
            receipt = json.loads(peer.stdout)
            self.assertEqual(receipt['result'], 'unknown', peer.stderr)
            self.assertIn('symlink', receipt['reason'].lower())
            self.assertFalse((physical_state / 'host-egress-snapshot').exists())
            self.assertFalse((self.root / 'calls').exists())
            self.assertIsNone(creator.poll(), 'creator was not held at the unsynced boundary')
        finally:
            creator.kill()
            creator.communicate(timeout=15)
            os.close(ready_read)
            os.close(release_write)

    def test_symlink_ancestors_and_loops_are_actionable_unknown(self):
        real = self.root / 'real'
        real.mkdir()
        (self.root / 'alias').symlink_to(real, target_is_directory=True)
        (self.root / 'loop').symlink_to(self.root / 'loop', target_is_directory=True)
        for state in (self.root / 'alias' / 'nested', self.root / 'loop' / 'nested'):
            with self.subTest(state=state):
                self.env['XDG_STATE_HOME'] = str(state)
                result = self.run_cli('record', 'symlink')
                self.assertEqual(result.returncode, 1, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt['result'], 'unknown')
                self.assertIn('symlink', receipt['reason'].lower())
                self.assertIn('XDG_STATE_HOME', receipt['reason'])
                self.assertFalse((self.root / 'calls').exists())
        self.assertFalse((real / 'nested').exists())

    def test_unrelated_symlinked_working_directory_is_supported(self):
        real = self.root / 'work'
        real.mkdir()
        alias = self.root / 'work-alias'
        alias.symlink_to(real, target_is_directory=True)
        result = subprocess.run([sys.executable, str(SCRIPT), 'record', 'cwd'],
                                env=dict(self.env, PWD=str(alias)), cwd=alias,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['result'], 'captured')

    def test_failed_existing_ancestor_sync_stops_before_publication(self):
        (self.root / 'state').mkdir(mode=0o700)
        result = self.fixture_cli('ancestor-sync-fail', 'record', 'ancestor')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertFalse((self.root / 'calls').exists())
        self.assertFalse((self.root / 'state/host-egress-snapshot').exists())

    def test_failed_baseline_publication_requires_read_durability_barrier(self):
        recorded = self.fixture_cli('baseline-dirsync-fail', 'record', 'sync')
        self.assertEqual(json.loads(recorded.stdout)['result'], 'incident_recorded_baseline_unknown',
                         recorded.stderr)
        directory = self.root / 'state/host-egress-snapshot'
        baseline = next(directory.glob('*.baseline'))
        calls = (self.root / 'calls').read_text()
        for fault in ('read-file-fail', 'read-dir-fail'):
            for mode in ('check', 'compare', 'refresh'):
                with self.subTest(fault=fault, mode=mode):
                    checked = self.fixture_cli(fault, mode, 'sync')
                    self.assertEqual(json.loads(checked.stdout)['result'], 'unknown', checked.stderr)
                    self.assertEqual((self.root / 'calls').read_text(), calls)
        checked = self.fixture_cli('sync-audit', 'check', 'sync')
        self.assertEqual(json.loads(checked.stdout)['result'], 'same', checked.stderr)
        synced = (self.root / 'sync-audit').read_text().splitlines()
        self.assertIn(str(baseline), synced)
        self.assertIn(str(directory), synced[synced.index(str(baseline)) + 1:])

    def test_first_use_under_restrictive_umask_and_normal_retry(self):
        p = subprocess.run([sys.executable, str(SCRIPT), 'record', 'masked'], env=self.env,
                           capture_output=True, text=True, timeout=30, umask=0o777)
        self.assertEqual(json.loads(p.stdout)['result'], 'captured', p.stderr)
        directory = self.root / 'state/host-egress-snapshot'
        self.assertEqual((directory / '.lock').stat().st_mode & 0o777, 0o600)
        self.assertEqual(next(directory.glob('*.baseline')).stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(self.run_cli('check', 'masked').stdout)['result'], 'same')

    def test_missing_passwd_entry_is_structured_unknown(self):
        command = [sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
                   str(self.root), 'missing-nss', 'refresh', 'a']
        p = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(p.stdout)['result'], 'unknown', p.stderr)
        self.assertIn('account', p.stdout.lower())
        self.assertNotIn('Traceback', p.stderr)

    def test_baseline_publication_failure_leaves_incident_not_baseline(self):
        command = [sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
                   str(self.root), 'baseline-failure', 'record', 'a']
        p = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(p.stdout)['result'], 'incident_recorded_baseline_unknown')
        directory = self.root / 'state/host-egress-snapshot'
        self.assertEqual(len(list(directory.glob('*.incident'))), 1)
        self.assertFalse(list(directory.glob('*.baseline')))
        self.assertFalse(list(directory.glob('.pending-*')))
        self.assertEqual(json.loads(self.run_cli('check', 'a').stdout)['result'], 'unknown')

    def test_concurrent_first_use_masked_and_insecure_lock_rejected(self):
        commands = [[sys.executable, str(SCRIPT), 'record', key] for key in ('x', 'y')]
        procs = [subprocess.Popen(cmd, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, umask=0o777) for cmd in commands]
        outputs = [p.communicate(timeout=30) for p in procs]
        self.assertEqual([json.loads(out)['result'] for out, err in outputs], ['captured', 'captured'], outputs)
        directory = self.root / 'state/host-egress-snapshot'
        self.assertEqual(len(list(directory.glob('*.baseline'))), 2)
        (directory / '.lock').chmod(0o000)
        p = self.run_cli('check', 'x')
        self.assertEqual(json.loads(p.stdout)['result'], 'unknown')
        self.assertEqual((directory / '.lock').stat().st_mode & 0o777, 0)

    def test_existing_collision_is_never_overwritten(self):
        directory = self.root / 'state/host-egress-snapshot'
        directory.mkdir(parents=True, mode=0o700)
        baseline = directory / (hashlib.sha256(b'incident-1').hexdigest() + '.baseline')
        baseline.symlink_to(self.root / 'victim')
        (self.root / 'victim').write_text('preserve')
        self.assertEqual(json.loads(self.run_cli('record').stdout)['result'], 'unknown')
        self.assertTrue(baseline.is_symlink())
        self.assertEqual((self.root / 'victim').read_text(), 'preserve')

    def test_concurrent_refreshes_share_existing_state_lock(self):
        for key in ('first', 'second'):
            self.assertEqual(self.run_cli('record', key).returncode, 0)
        (self.root / 'response').write_text('ip=9.9.9.9\n')
        calls_before = (self.root / 'calls').read_text()
        lock = self.root / 'state/host-egress-snapshot/.lock'
        with lock.open('r+') as holder:
            fcntl.flock(holder, fcntl.LOCK_EX)
            procs = [subprocess.Popen([sys.executable, str(SCRIPT.parents[3] / 'tests/refresh_fixture_launcher.py'),
                                       str(self.root), 'production', 'refresh', key], env=self.env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for key in ('first', 'second')]
            try:
                time.sleep(.3)
                self.assertTrue(all(p.poll() is None for p in procs))
                self.assertEqual((self.root / 'calls').read_text(), calls_before)
            finally:
                fcntl.flock(holder, fcntl.LOCK_UN)
                results = [p.communicate(timeout=30) for p in procs]
        self.assertEqual([json.loads(out)['result'] for out, err in results],
                         ['already_refreshed', 'already_refreshed'])
        calls = (self.root / 'calls').read_text()
        self.assertNotIn('tailscale set ', calls)
        self.assertNotIn('mullvad reconnect', calls)

    def test_refresh_missing_baseline_and_unsafe_route_never_switch(self):
        missing = self.run_cli('refresh')
        self.assertEqual(json.loads(missing.stdout)['result'], 'unknown')
        self.assertFalse((self.root / 'calls').exists())
        self.assertEqual(self.run_cli('record').returncode, 0)
        self.replies['ip -4 route get 1.1.1.1'] = '1.1.1.1 dev eth0'
        self.setup_tools()
        (self.root / 'calls').unlink()
        unsafe = self.run_cli('refresh')
        self.assertEqual(json.loads(unsafe.stdout)['result'], 'unknown')
        calls = (self.root / 'calls').read_text()
        self.assertNotIn('curl ', calls)
        self.assertNotIn('tailscale set ', calls)
        self.assertNotIn('mullvad reconnect', calls)

    def test_capture_then_compare_without_exposing_ip(self):
        capture = self.run_cli('capture')
        self.assertEqual(capture.returncode, 0, capture.stderr)
        self.assertEqual(json.loads(capture.stdout)['result'], 'captured')
        same = self.run_cli('compare')
        self.assertEqual(json.loads(same.stdout)['result'], 'same')
        (self.root / 'response').write_text('ip=9.9.9.9\n')
        different = self.run_cli('compare')
        self.assertEqual(json.loads(different.stdout)['result'], 'different')
        for p in (capture, same, different):
            self.assertNotIn('8.8.8.8', p.stdout + p.stderr)
            self.assertNotIn('9.9.9.9', p.stdout + p.stderr)
            self.assertEqual(json.loads(p.stdout)['path'], 'host-direct')
            self.assertEqual(json.loads(p.stdout)['action'], 'none')

    def test_invalid_baseline_is_preserved_without_sampling(self):
        directory = self.root / 'state/host-egress-snapshot'
        directory.mkdir(parents=True, mode=0o700)
        baseline = directory / (hashlib.sha256(b'incident-1').hexdigest() + '.baseline')
        cases = (b'8.8.8.8', b'8.8.8.80', b'8.8.8.8\r\n', b'8.8.8.8\n ',
                 b'8.8.8.8\njunk', b'8.8.8.8\n9.9.9.9\n',
                 b'123.123.123.123\nx', b'8.8.8.8' + b' ' * 57 + b'junk',
                 b'10.0.0.1\n', b'192.88.99.2\n', b'224.0.0.1\n', b'\xff')
        for data in cases:
            with self.subTest(data=data):
                baseline.write_bytes(data)
                baseline.chmod(0o600)
                (self.root / 'calls').unlink(missing_ok=True)
                result = self.run_cli('compare')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
                self.assertEqual(baseline.read_bytes(), data)
                self.assertFalse((self.root / 'calls').exists())

    def test_max_length_valid_baseline_compares_normally(self):
        (self.root / 'response').write_text('ip=123.123.123.123\n')
        self.assertEqual(json.loads(self.run_cli('capture').stdout)['result'], 'captured')
        result = self.run_cli('compare')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['result'], 'same')

    def test_curl_contract_and_clean_environment(self):
        result = self.run_cli('capture')
        self.assertEqual(result.returncode, 0, result.stdout)
        calls = (self.root / 'calls').read_text().splitlines()
        curl = [x for x in calls if x.startswith('curl ')]
        self.assertEqual(curl, ['curl --disable --noproxy * --interface tailscale0 -4 --proto =https --connect-timeout 5 --max-time 15 --max-filesize 4096 -fsS https://1.1.1.1/cdn-cgi/trace'])
        env = json.loads((self.root / 'curl-env').read_text())
        self.assertNotIn('HTTPS_PROXY', env)
        self.assertNotIn('http_proxy', env)
        self.assertNotIn('SSL_CERT_FILE', env)
        directory = self.root / 'state/host-egress-snapshot'
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(next(directory.glob('*.baseline')).stat().st_mode & 0o777, 0o600)

    def test_reject_bad_response_without_leaking_it(self):
        for response in ('ip=10.0.0.1', 'ip=192.88.99.2', 'ip=::1', 'ip=8.8.8.8\nip=8.8.8.8', 'ip=bad', 'x' * 5000):
            with self.subTest(response=response[:30]):
                (self.root / 'response').write_text(response)
                result = self.run_cli('capture')
                self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
                self.assertNotIn(response[:20], result.stdout + result.stderr)
                self.assertFalse(list((self.root / 'state/host-egress-snapshot').glob('*.baseline')))

    def test_multicast_probe_is_rejected_without_baseline(self):
        (self.root / 'response').write_text('ip=224.0.0.1\n')
        result = self.run_cli('capture')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertFalse(list((self.root / 'state/host-egress-snapshot').glob('*.baseline')))

    def test_failed_curl_also_rechecks_manager(self):
        (self.root / 'curl-fail').touch()
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        calls = (self.root / 'calls').read_text().splitlines()
        self.assertEqual(calls.count('ip -4 route get 1.1.1.1'), 2)

    def test_unsafe_manager_never_probes(self):
        self.replies['ip -4 route get 1.1.1.1'] = '1.1.1.1 dev eth0'
        self.setup_tools()
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertIn('ipv4-route-conflict', json.loads(result.stdout)['reason'])
        self.assertNotIn('curl ', (self.root / 'calls').read_text())

    def test_failed_manager_preflight_identifies_safe_component(self):
        self.replies['mullvad status --json'] = 'invalid-json-with-secret-canary'
        self.setup_tools()
        result = self.run_cli('capture')
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['result'], 'unknown')
        self.assertIn('mullvad-status-invalid', receipt['reason'])
        self.assertNotIn('secret-canary', result.stdout + result.stderr)
        self.assertNotIn('curl ', (self.root / 'calls').read_text())

    def test_post_probe_route_and_peer_drift_are_unknown(self):
        for key, value in [('ip -4 route get 1.1.1.1', '1.1.1.1 dev tailscale0 table 53'),
                           ('tailscale get exit-node', '100.96.176.47')]:
            with self.subTest(key=key):
                (self.root / 'drift.json').write_text(json.dumps(self.replies | {key: value}))
                result = self.run_cli('capture')
                self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
                self.assertFalse(list((self.root / 'state/host-egress-snapshot').glob('*.baseline')))
                self.setup_tools()

    def test_missing_manager_cli_never_probes(self):
        (self.bin / 'mullvad').unlink()
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertNotIn('curl ', (self.root / 'calls').read_text())

    def test_missing_cli_no_baseline_and_duplicate_capture(self):
        result = self.run_cli('compare')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertFalse((self.root / 'calls').exists())
        (self.bin / 'curl').unlink()
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertIn('curl unavailable', result.stdout)
        self.setup_tools()
        self.assertEqual(self.run_cli('capture').returncode, 0)
        calls_before = (self.root / 'calls').read_text()
        self.assertEqual(json.loads(self.run_cli('capture').stdout)['result'], 'unknown')
        self.assertEqual((self.root / 'calls').read_text(), calls_before)

    def test_mullvad_details_without_relay_identity_never_probes(self):
        self.replies.update({'tailscale get exit-node': '',
            'tailscale status --json': json.dumps({'BackendState': 'Running'}),
            'tailscale debug prefs': json.dumps({'RouteAll': False, 'ExitNodeID': ''}),
            'mullvad status --json': json.dumps({'state': 'connected', 'details': {'location': {'country': 'US'}}}),
            'ip -4 route get 1.1.1.1': '1.1.1.1 dev wg-mullvad'})
        self.setup_tools()
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertNotIn('curl ', (self.root / 'calls').read_text())

    def test_standalone_mullvad(self):
        self.replies.update({'tailscale get exit-node': '',
            'tailscale status --json': json.dumps({'BackendState': 'Running'}),
            'tailscale debug prefs': json.dumps({'RouteAll': False, 'ExitNodeID': ''}),
            'mullvad status --json': json.dumps({'state': 'connected', 'details': {'location': {'hostname': 'fixture-relay'}}}),
            'ip -4 route get 1.1.1.1': '1.1.1.1 dev wg-mullvad'})
        self.setup_tools()
        result = self.run_cli('capture')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('--interface wg-mullvad', (self.root / 'calls').read_text())

    def test_mullvad_relay_drift_is_unknown(self):
        self.replies.update({'tailscale get exit-node': '',
            'tailscale status --json': json.dumps({'BackendState': 'Running'}),
            'tailscale debug prefs': json.dumps({'RouteAll': False, 'ExitNodeID': ''}),
            'mullvad status --json': json.dumps({'state': 'connected', 'details': {'location': {'hostname': 'first'}}}),
            'ip -4 route get 1.1.1.1': '1.1.1.1 dev wg-mullvad'})
        self.setup_tools()
        changed = self.replies | {'mullvad status --json': json.dumps({'state': 'connected', 'details': {'location': {'hostname': 'second'}}})}
        (self.root / 'drift.json').write_text(json.dumps(changed))
        result = self.run_cli('capture')
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertFalse(list((self.root / 'state/host-egress-snapshot').glob('*.baseline')))

    def test_same_key_concurrency_has_one_capture(self):
        cmd = [sys.executable, str(SCRIPT), 'capture', 'concurrent']
        procs = [subprocess.Popen(cmd, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        results = [p.communicate(timeout=30) for p in procs]
        self.assertCountEqual([json.loads(out)['result'] for out, _ in results], ['captured', 'unknown'])
        self.assertEqual(sum(x.startswith('curl ') for x in (self.root / 'calls').read_text().splitlines()), 1)
        self.assertEqual(len(list((self.root / 'state/host-egress-snapshot').glob('*.baseline'))), 1)

    def test_skill_symlink_from_other_directory(self):
        installed = self.root / 'installed/script-manager'
        installed.parent.mkdir()
        installed.symlink_to(SCRIPT.parents[1], target_is_directory=True)
        result = subprocess.run([sys.executable, str(installed / 'scripts/egress_snapshot.py'), 'capture', 'symlink'],
                                env=self.env, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_insecure_state_directory_and_file_are_rejected(self):
        self.assertEqual(self.run_cli('capture').returncode, 0)
        directory = self.root / 'state/host-egress-snapshot'
        baseline = next(directory.glob('*.baseline'))
        baseline.chmod(0o644)
        self.assertEqual(json.loads(self.run_cli('compare').stdout)['result'], 'unknown')
        baseline.chmod(0o600)
        directory.chmod(0o755)
        self.assertEqual(json.loads(self.run_cli('compare').stdout)['result'], 'unknown')

if __name__ == '__main__':
    unittest.main()
