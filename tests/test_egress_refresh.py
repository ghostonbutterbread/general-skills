"""Real child CLI rotation fixtures; run under egress_offline_runner.py only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / 'tests/refresh_fixture_launcher.py'


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = {'PATH': str(self.bin), 'HOME': str(self.root), 'TMPDIR': str(self.root),
                    'XDG_STATE_HOME': str(self.root / 'state'), 'PYTHONDONTWRITEBYTECODE': '1'}
        (self.root / 'relay-list').write_text((ROOT / 'tests/fixtures/mullvad-relay-list.txt').read_text())
        tool = '''#!{python} -s
import json, os, sys, time
from pathlib import Path
r = Path({root!r})
cmd = Path(sys.argv[0]).name + ' ' + ' '.join(sys.argv[1:])
with (r/'calls').open('a') as f: f.write(cmd+'\\n')
s = json.loads((r/'fixture.json').read_text())
def peer(n):
    city = 'Portland, OR' if (r/'wrong-city').exists() and s['n'] == 2 and n == 2 else 'Seattle, WA'
    return {{'ID':'node'+str(n),'HostName':f'us-sea-wg-{{n}}','DNSName':f'us-sea-wg-{{n}}.mullvad.ts.net.', 'Online':True,'ExitNodeOption':True,'Tags':['tag:mullvad-exit-node'],'TailscaleIPs':[f'100.96.176.{{n}}/32'],'Location':{{'Country':'USA','CountryCode':'US','City':city}}}}
n=s['n']; p=peer(n); standalone = s.get('manager') == 'mullvad'
if cmd == 'tailscale get exit-node': print('' if standalone else f'100.96.176.{{n}}')
elif cmd == 'tailscale status --json': print(json.dumps({{'BackendState':'Running', **({{}} if standalone else {{'ExitNodeStatus':{{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs']}},'Peer':{{str(i):peer(i) for i in (1,2)}}}})}}))
elif cmd == 'tailscale debug prefs': print(json.dumps({{'RouteAll':False,'ExitNodeID':'' if standalone else p['ID']}}))
elif cmd == 'mullvad status --json':
    print(json.dumps({{'state':'connected','details':{{'location':{{'country':'USA','city':'Seattle, WA','hostname':f'us-sea-wg-{{n}}','entry_hostname':None,'obfuscator_hostname':None}}}}}}) if standalone else '{{"state":"disconnected"}}')
elif cmd == 'ip -4 route get 1.1.1.1':
    interface = 'eth0' if (r/'wrong-route').exists() and n == 2 else ('wg-mullvad' if standalone else 'tailscale0')
    print('1.1.1.1 dev ' + interface + ' table 52')
elif cmd == 'mullvad relay list':
    print((r/'relay-list').read_text().replace('us-sea-wg-001', 'us-sea-wg-1').replace('us-sea-wg-002', 'us-sea-wg-2').replace('us-sea-wg-003', 'us-sea-wg-3').replace('us-sea-wg-4', 'us-sea-wg-9'))
elif cmd == 'mullvad relay set location us sea us-sea-wg-2': pass
elif cmd == 'mullvad reconnect --wait':
    s.update(n=2,ip='9.9.9.9'); (r/'fixture.json').write_text(json.dumps(s))
elif cmd == 'curl ' + ' '.join(sys.argv[1:]): print('ip='+s['ip'])
elif cmd == 'tailscale exit-node list --filter=USA':
    print('IP HOSTNAME COUNTRY CITY')
    for i in (1,2): print(f'100.96.176.{{i}} us-sea-wg-{{i}}.mullvad.ts.net USA {{peer(i)["Location"]["City"]}} '+('selected' if i==n else '-'))
elif cmd.startswith('tailscale set --exit-node='):
    (r/'switch-started').touch()
    while (r/'hold').exists(): time.sleep(.02)
    if (r/'fail').exists(): sys.exit(1)
    target = 1 if 'us-sea-wg-1.' in cmd else 2
    if (r/'wrong-target').exists(): target = 1
    s.update(n=target,ip=('8.8.8.8' if (r/'same-ip').exists() else ('9.9.9.9' if target == 2 else '8.8.4.4')))
    if (r/'wrong-manager').exists(): s['manager'] = 'mullvad'
    (r/'fixture.json').write_text(json.dumps(s)); (r/'switch-finished').touch()
else: sys.exit(2)
'''.format(python=sys.executable, root=str(self.root))
        for name in ('tailscale', 'mullvad', 'ip', 'curl'):
            path = self.bin / name
            path.write_text(tool)
            path.chmod(0o700)
        (self.root / 'fixture.json').write_text(json.dumps({'n': 1, 'ip': '8.8.8.8'}))

    def start(self, mode, key='a', env=None):
        return subprocess.Popen([sys.executable, str(LAUNCH), str(self.root), 'production', mode, key],
                                env=env or self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def run_cli(self, mode, key='a', env=None):
        p = self.start(mode, key, env)
        out, err = p.communicate(timeout=90)
        self.assertTrue(out, err)
        return json.loads(out)

    def inject_after_switch(self, name, condition, action):
        tool = self.bin / name
        text = tool.read_text()
        anchor = "if cmd == 'tailscale get exit-node': print('' if standalone else f'100.96.176.{n}')"
        self.assertIn(anchor, text)
        text = text.replace(anchor, "if (r/'switch-finished').exists() and " + condition + ":\n    " + action + "\n" + anchor, 1)
        tool.write_text(text)

    def test_conflicting_exit_identity_blocks_preflight_without_probe_or_switch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        tool = self.bin / 'tailscale'
        text = tool.read_text()
        old = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs']}"
        new = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs'],'HostName':'us-sea-wg-2'}"
        self.assertIn(old, text)
        tool.write_text(text.replace(old, new))
        calls_before = len((self.root/'calls').read_text().splitlines())
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action']), ('unknown', 'none'))
        calls = (self.root/'calls').read_text().splitlines()[calls_before:]
        self.assertFalse(any(c.startswith(('curl ', 'tailscale set ')) for c in calls))
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_conflicting_exit_identity_after_switch_blocks_probe_and_keeps_latch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        tool = self.bin / 'tailscale'
        text = tool.read_text()
        old = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs']}"
        new = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs'], **({'HostName':'us-sea-wg-1'} if n==2 else {})}"
        self.assertIn(old, text)
        tool.write_text(text.replace(old, new))
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action'], result['stage']),
                         ('unknown', 'switch_uncertain', 'local_verification'))
        calls = (self.root/'calls').read_text().splitlines()
        switch = next(i for i, c in enumerate(calls) if c.startswith('tailscale set '))
        self.assertFalse(any(c.startswith('curl ') for c in calls[switch+1:]))
        self.assertEqual(sum(c.startswith('tailscale set ') for c in calls), 1)
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_selection_observation_conflict_stops_before_reprobe_or_switch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        (self.root/'calls').write_text('')
        tool = self.bin / 'tailscale'
        text = tool.read_text()
        old = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs']}"
        new = ("'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs'], "
               "**({'HostName':'us-sea-wg-2'} if (r/'calls').read_text().splitlines().count('tailscale status --json') == 3 else {})}")
        self.assertIn(old, text)
        tool.write_text(text.replace(old, new))
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action']), ('unknown', 'none'))
        calls = (self.root/'calls').read_text().splitlines()
        status_indices = [i for i, c in enumerate(calls) if c == 'tailscale status --json']
        self.assertEqual(len(status_indices), 3)
        self.assertFalse(any(c.startswith(('curl ', 'tailscale set ')) for c in calls[status_indices[2]+1:]))
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_verify_observation_conflict_stops_post_switch_probe(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        tool = self.bin / 'tailscale'
        text = tool.read_text()
        old = "'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs']}"
        new = ("'ExitNodeStatus':{'ID':p['ID'],'Online':True,'TailscaleIPs':p['TailscaleIPs'], "
               "**({'HostName':'us-sea-wg-1'} if n==2 and "
               "(r/'calls').read_text().rsplit('tailscale set --exit-node=', 1)[-1].splitlines().count('tailscale status --json') % 2 == 0 else {})}")
        self.assertIn(old, text)
        tool.write_text(text.replace(old, new))
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action'], result['stage']),
                         ('unknown', 'switch_uncertain', 'local_verification'))
        calls = (self.root/'calls').read_text().splitlines()
        switch = next(i for i, c in enumerate(calls) if c.startswith('tailscale set '))
        self.assertFalse(any(c.startswith('curl ') for c in calls[switch+1:]))
        self.assertEqual(sum(c.startswith('tailscale set ') for c in calls), 1)
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_transient_post_switch_probe_retries_without_reswitch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        tool = self.bin / 'curl'
        text = tool.read_text()
        anchor = "if cmd == 'tailscale get exit-node': print('' if standalone else f'100.96.176.{n}')"
        self.assertIn(anchor, text)
        text = text.replace(anchor, "if (r/'switch-finished').exists() and not (r/'transient-fired').exists() and cmd.startswith('curl '):\n    (r/'transient-fired').touch(); sys.exit(7)\n" + anchor, 1)
        tool.write_text(text)
        result = self.run_cli('refresh')
        self.assertEqual(result['result'], 'refreshed')
        self.assertTrue((self.root/'transient-fired').exists())
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_transient_stale_ip_and_selection_recover(self):
        for fault in ('old-ip', 'old-selection'):
            with self.subTest(fault=fault):
                (self.root/'fixture.json').write_text(json.dumps({'n': 1, 'ip': '8.8.8.8'}))
                (self.root/'switch-finished').unlink(missing_ok=True)
                (self.root/'transient-fired').unlink(missing_ok=True)
                self.assertEqual(self.run_cli('record', fault)['result'], 'captured')
                name = 'curl' if fault == 'old-ip' else 'tailscale'
                original = (self.bin/name).read_text()
                command = "cmd.startswith('curl ')" if fault == 'old-ip' else "cmd == 'tailscale get exit-node'"
                value = 'ip=8.8.8.8' if fault == 'old-ip' else '100.96.176.1'
                self.inject_after_switch(name, "not (r/'transient-fired').exists() and " + command,
                                         "(r/'transient-fired').touch(); print(" + repr(value) + "); sys.exit(0)")
                result = self.run_cli('refresh', fault)
                self.assertEqual(result['result'], 'refreshed')
                self.assertTrue((self.root/'transient-fired').exists())
                self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())
                (self.bin/name).write_text(original)
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 2)

    def test_persistent_unsafe_route_never_probes_after_switch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        (self.root/'wrong-route').touch()
        start = time.monotonic()
        result = self.run_cli('refresh')
        self.assertLess(time.monotonic() - start, 30)
        self.assertEqual((result['stage'], result['error_code']), ('local_verification', 'observation_invalid'))
        self.assertGreaterEqual(result['attempts'], 1)
        self.assertLessEqual(result['attempts'], 3)
        calls = (self.root/'calls').read_text().splitlines()
        switch = next(i for i, c in enumerate(calls) if c.startswith('tailscale set '))
        self.assertFalse(any(c.startswith('curl ') for c in calls[switch+1:]))
        self.assertEqual(sum(c.startswith('tailscale set ') for c in calls), 1)
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_persistent_probe_failure_has_sanitized_stage(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        self.inject_after_switch('curl', "cmd.startswith('curl ')", "print('private-canary', file=sys.stderr); sys.exit(7)")
        result = self.run_cli('refresh')
        self.assertEqual((result['stage'], result['error_code'], result['attempts']), ('host_probe', 'probe_failed', 3))
        self.assertNotIn('private-canary', json.dumps(result))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_transient_drift_after_probe_requires_fresh_complete_attempt(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        self.inject_after_switch('curl', "cmd.startswith('curl ') and not (r/'sampled').exists()",
                                 "(r/'sampled').touch(); print('ip='+s['ip']); sys.exit(0)")
        self.inject_after_switch('tailscale', "cmd == 'tailscale get exit-node' and (r/'sampled').exists() and not (r/'transient-fired').exists()",
                                 "(r/'transient-fired').touch(); print('100.96.176.1'); sys.exit(0)")
        result = self.run_cli('refresh')
        self.assertEqual(result['result'], 'refreshed')
        self.assertTrue((self.root/'transient-fired').exists())
        calls = (self.root/'calls').read_text().splitlines()
        switch = next(i for i, c in enumerate(calls) if c.startswith('tailscale set '))
        self.assertEqual(sum(c.startswith('curl ') for c in calls[switch+1:]), 2)
        self.assertEqual(sum(c.startswith('tailscale set ') for c in calls), 1)
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_slow_local_observation_obeys_deadline_and_never_probes(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        self.inject_after_switch('tailscale', "cmd == 'tailscale get exit-node'", "time.sleep(30)")
        start = time.monotonic()
        result = self.run_cli('refresh')
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 25)
        self.assertEqual((result['action'], result['stage']), ('switch_uncertain', 'local_verification'))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        calls = (self.root/'calls').read_text().splitlines()
        switch = next(i for i, c in enumerate(calls) if c.startswith('tailscale set '))
        self.assertFalse(any(c.startswith('curl ') for c in calls[switch+1:]))
        self.assertEqual(sum(c.startswith('tailscale set ') for c in calls), 1)

    def test_manager_drift_after_probe_is_not_success(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        self.inject_after_switch('curl', "cmd.startswith('curl ')",
                                 "s['manager']='mullvad'; (r/'fixture.json').write_text(json.dumps(s)); print('ip='+s['ip']); sys.exit(0)")
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action'], result['stage']), ('unknown', 'switch_uncertain', 'local_verification'))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_drift_after_probe_is_not_success(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        self.inject_after_switch('curl', "cmd.startswith('curl ')", "(r/'wrong-route').touch(); print('ip='+s['ip']); sys.exit(0)")
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action'], result['stage']), ('unknown', 'switch_uncertain', 'local_verification'))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_first_rotation_lock_under_restrictive_umask(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        p = subprocess.run([sys.executable, str(LAUNCH), str(self.root), 'production', 'refresh', 'a'],
                           env=self.env, capture_output=True, text=True, timeout=90, umask=0o777)
        self.assertEqual(json.loads(p.stdout)['result'], 'refreshed', p.stderr)
        lock = self.root/'.host-egress-rotation/.lock'
        self.assertEqual(lock.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.run_cli('refresh')['result'], 'already_refreshed')

    def test_production_admission_switches_after_verified_observations(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        p = subprocess.run([sys.executable, str(LAUNCH), str(self.root), 'production', 'refresh', 'a'],
                           env=self.env, capture_output=True, text=True, timeout=90)
        receipt = json.loads(p.stdout)
        self.assertEqual((receipt['result'], receipt['action']), ('refreshed', 'switch'), p.stderr)
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_environment_cannot_bypass_unknown_route(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        env = dict(self.env, EGRESS_ALLOW_ROTATION='1', EGRESS_PROTECTED='1')
        (self.root/'fixture.json').write_text(json.dumps({'n': 2, 'ip': '8.8.8.8'}))
        (self.root/'wrong-route').touch()
        cmd = [sys.executable, str(LAUNCH), str(self.root), 'production', 'refresh', 'a']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(result.stdout)['result'], 'unknown')
        self.assertNotIn('tailscale set ', (self.root/'calls').read_text())
        self.assertFalse((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_crash_does_not_allow_retry_while_switch_child_continues(self):
        self.assertEqual(self.run_cli('record', 'a')['result'], 'captured')
        self.assertEqual(self.run_cli('record', 'b')['result'], 'captured')
        (self.root/'hold').touch()
        first = self.start('refresh', 'a')
        try:
            end = time.monotonic()+15
            while not (self.root/'switch-started').exists() and time.monotonic()<end:
                time.sleep(.02)
            self.assertTrue((self.root/'switch-started').exists())
            first.kill()
            first.communicate(timeout=10)
            self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
            self.assertEqual(self.run_cli('refresh', 'b')['result'], 'unknown')
        finally:
            (self.root/'hold').unlink(missing_ok=True)
            if first.poll() is None:
                first.kill(); first.communicate(timeout=10)
            end = time.monotonic()+10
            while (self.root/'switch-started').exists() and not (self.root/'switch-finished').exists() and time.monotonic()<end:
                time.sleep(.02)
        self.assertTrue((self.root/'switch-finished').exists())
        self.assertEqual(self.run_cli('refresh', 'b')['result'], 'unknown')
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_post_switch_identity_and_city_mismatch_latches(self):
        for fault in ('wrong-target', 'wrong-city', 'wrong-manager', 'wrong-route'):
            with self.subTest(fault=fault):
                (self.root/'fixture.json').write_text(json.dumps({'n': 1, 'ip': '8.8.8.8'}))
                key = 'case-' + fault
                self.assertEqual(self.run_cli('record', key)['result'], 'captured')
                (self.root/fault).touch()
                result = self.run_cli('refresh', key)
                self.assertEqual((result['result'], result['action']), ('unknown', 'switch_uncertain'))
                latch = self.root/'.host-egress-rotation/rotation-incomplete'
                self.assertTrue(latch.exists())
                # Test-only reset after fake CLI has exited.
                latch.unlink()
                (self.root/fault).unlink()

    def test_post_switch_malformed_peer_keeps_latch_and_structured_receipt(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        tool = self.bin / 'tailscale'
        text = tool.read_text()
        old = "'Peer':{str(i):peer(i) for i in (1,2)}"
        new = "'Peer':({'bad':'malformed', **{str(i):peer(i) for i in (1,2)}} if n==2 else {str(i):peer(i) for i in (1,2)})"
        self.assertIn(old, text)
        tool.write_text(text.replace(old, new))
        p = self.start('refresh')
        out, err = p.communicate(timeout=90)
        self.assertEqual((json.loads(out)['result'], json.loads(out)['action']),
                         ('unknown', 'switch_uncertain'), err)
        self.assertNotIn('Traceback', err)
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_unchanged_ip_after_switch_latches(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        (self.root/'same-ip').touch()
        result = self.run_cli('refresh')
        self.assertEqual((result['result'], result['action']), ('unknown', 'switch_uncertain'))
        self.assertEqual((result['stage'], result['error_code'], result['attempts']), ('stale_ip', 'address_unchanged', 3))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())

    def test_unexpected_exceptions_distinguish_before_and_after_switch(self):
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        for fault, action, latch in (('pre-exception', 'none', False),
                                     ('post-exception', 'switch_uncertain', True)):
            p = subprocess.run([sys.executable, str(LAUNCH), str(self.root), fault, 'refresh', 'a'],
                               env=self.env, capture_output=True, text=True, timeout=90)
            receipt = json.loads(p.stdout)
            self.assertEqual((receipt['result'], receipt['action']), ('unknown', action))
            if fault == 'post-exception':
                self.assertEqual((receipt['stage'], receipt['error_code'], receipt['attempts']),
                                 ('local_verification', 'unexpected_error', 1))
            self.assertNotIn('canary', p.stdout + p.stderr)
            self.assertNotIn('Traceback', p.stderr)
            self.assertEqual((self.root/'.host-egress-rotation/rotation-incomplete').exists(), latch)

    def test_fsync_failures_classify_mutation_and_keep_latch(self):
        for fault, action in (('pre-sync', 'none'), ('post-sync', 'switch_uncertain')):
            with self.subTest(fault=fault):
                (self.root/'fixture.json').write_text(json.dumps({'n': 1, 'ip': '8.8.8.8'}))
                (self.root/'switch-started').unlink(missing_ok=True)
                key = 'sync-' + fault
                self.assertEqual(self.run_cli('record', key)['result'], 'captured')
                p = subprocess.run([sys.executable, str(LAUNCH), str(self.root), fault, 'refresh', key],
                                   env=self.env, capture_output=True, text=True, timeout=90)
                self.assertEqual((json.loads(p.stdout)['result'], json.loads(p.stdout)['action']),
                                 ('unknown', action), p.stderr)
                latch = self.root/'.host-egress-rotation/rotation-incomplete'
                self.assertTrue(latch.exists())
                self.assertEqual((self.root/'switch-started').exists(), fault == 'post-sync')
                latch.unlink()

    def test_record_after_another_change_is_a_new_baseline(self):
        self.assertEqual(self.run_cli('record', 'a')['result'], 'captured')
        self.assertEqual(self.run_cli('refresh', 'a')['result'], 'refreshed')
        self.assertEqual(self.run_cli('record', 'late')['result'], 'captured')
        self.assertEqual(self.run_cli('refresh', 'late')['result'], 'refreshed')
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 2)

    def test_standalone_same_city_switch(self):
        (self.root/'fixture.json').write_text(json.dumps({'n': 1, 'ip': '8.8.8.8', 'manager': 'mullvad'}))
        self.assertEqual(self.run_cli('record')['result'], 'captured')
        result = self.run_cli('refresh')
        self.assertEqual(result['result'], 'refreshed')
        calls = (self.root/'calls').read_text()
        self.assertIn('mullvad relay set location us sea us-sea-wg-2', calls)
        self.assertEqual(calls.count('mullvad reconnect --wait'), 1)
        self.assertNotIn('tailscale set ', calls)
        self.assertNotIn('mullvad disconnect', calls)

    def test_failed_switch_latches_and_blocks_new_incident(self):
        self.assertEqual(self.run_cli('record', 'a')['result'], 'captured')
        self.assertEqual(self.run_cli('record', 'b')['result'], 'captured')
        (self.root/'fail').touch()
        failed = self.run_cli('refresh', 'a')
        self.assertEqual(failed['result'], 'unknown')
        self.assertEqual(failed['action'], 'switch_uncertain')
        self.assertEqual((failed['stage'], failed['error_code'], failed['attempts']), ('manager_command', 'command_failed', 0))
        self.assertTrue((self.root/'.host-egress-rotation/rotation-incomplete').exists())
        self.assertEqual(self.run_cli('refresh', 'b')['result'], 'unknown')
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)

    def test_same_manager_switch_and_concurrent_dedup_across_xdg_roots(self):
        self.assertEqual(self.run_cli('record', 'a')['result'], 'captured')
        other = dict(self.env, XDG_STATE_HOME=str(self.root/'other-state'))
        self.assertEqual(self.run_cli('record', 'b', other)['result'], 'captured')
        (self.root/'hold').touch()
        first = self.start('refresh', 'a')
        end = time.monotonic()+15
        while not (self.root/'switch-started').exists() and time.monotonic()<end:
            time.sleep(.02)
        if not (self.root/'switch-started').exists():
            out, err = first.communicate(timeout=30)
            self.fail(out + err)
        (self.root/'launcher-ready-b').unlink()
        calls_before = (self.root/'calls').read_text()
        second = self.start('refresh', 'b', other)
        end = time.monotonic() + 10
        while not (self.root/'launcher-ready-b').exists() and time.monotonic() < end:
            time.sleep(.02)
        self.assertTrue((self.root/'launcher-ready-b').exists())
        time.sleep(.2)
        self.assertIsNone(second.poll())
        self.assertEqual((self.root/'calls').read_text(), calls_before)
        (self.root/'hold').unlink()
        a, ae = first.communicate(timeout=30); b, be = second.communicate(timeout=30)
        self.assertEqual(json.loads(a)['result'], 'refreshed', ae)
        self.assertEqual(json.loads(b)['result'], 'already_refreshed', be)
        self.assertEqual((self.root/'calls').read_text().count('tailscale set --exit-node='), 1)
        self.assertNotIn('mullvad disconnect', (self.root/'calls').read_text())
