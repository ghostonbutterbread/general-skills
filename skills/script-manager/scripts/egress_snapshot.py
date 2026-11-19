#!/usr/bin/env python3
"""Capture or compare a private host-direct IPv4 incident baseline.

Optional refresh may switch to a same-manager, same-city VPN exit after checks.
These checks are point-in-time only and do not guarantee continuous VPN
protection or recovery access.
"""
import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
import pwd
from pathlib import Path
import selectors
import stat
import subprocess
import tempfile
import time

import egress_inspect

ENDPOINT = 'https://1.1.1.1/cdn-cgi/trace'
POST_SWITCH_TIMEOUT = 15.0
POST_SWITCH_ATTEMPTS = 3
POST_SWITCH_RETRY_DELAY = 0.2


class Unknown(Exception):
    pass


class SwitchUncertain(Unknown):
    def __init__(self, reason, stage, error, attempts):
        super().__init__(reason)
        self.stage = stage
        self.error = error
        self.attempts = attempts


class IncidentRecorded(Unknown):
    pass


def private_file(path, flags):
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
        os.close(fd)
        raise Unknown('State file is not private; inspect state directory permissions.')
    return fd


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_mkdir(path):
    # Even an existing ancestor may have just been made by a peer which has
    # not yet synced its parent. Each caller establishes the complete chain.
    if path == path.parent:
        return
    durable_mkdir(path.parent)
    # A lexical parent chain can omit the physical parent of a symlink target,
    # so it cannot establish the target entry's durability after a peer mkdir.
    if path.is_symlink():
        raise Unknown('State path contains a symlink; use an absolute XDG_STATE_HOME without symlink components and retry.')
    if not path.is_dir():
        path.mkdir(mode=0o700, exist_ok=True)
    sync_directory(path.parent)


def state_dir():
    base = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state')
    if not base.is_absolute():
        raise Unknown('XDG_STATE_HOME must be absolute.')
    directory = base / 'host-egress-snapshot'
    durable_mkdir(directory)
    info = directory.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise Unknown('State directory must be owner-owned and mode 0700.')
    sync_directory(base)
    return directory


def snapshot():
    # Capture the canonical inspector's actual observations without duplicating
    # its manager classification. Raw details never leave process memory.
    observed = {}
    original = egress_inspect.run
    def collect(*args):
        result = original(*args)
        observed[args] = result
        return result
    egress_inspect.run = collect
    try:
        status = egress_inspect.inspect_host()
    finally:
        egress_inspect.run = original
    if status['manager'] not in ('tailscale', 'mullvad') or status['issues']:
        issues = ', '.join(status['issues']) or 'no active verified VPN manager'
        raise Unknown(f'VPN manager or destination route is unsafe or unknown ({issues}); inspect local egress.')
    route = observed[('ip', '-4', 'route', 'get', '1.1.1.1')][1]
    raw = observed[('mullvad', 'status', '--json')][1]
    mullvad = json.loads(raw)
    if status['manager'] == 'mullvad':
        details = mullvad.get('details')
        if not isinstance(details, dict):
            raise Unknown('Connected Mullvad relay identity unavailable; inspect local egress.')
        location, endpoint = details.get('location'), details.get('endpoint')
        hostname = location.get('hostname') if isinstance(location, dict) else None
        address = endpoint.get('address') if isinstance(endpoint, dict) else None
        if not any(isinstance(value, str) and value.strip() for value in (hostname, address)):
            raise Unknown('Connected Mullvad relay identity unavailable; inspect local egress.')
    return (status['manager'], status['tailscale'], status['route'], route, mullvad)


def public_ipv4(value):
    address = ipaddress.IPv4Address(value)
    if (not address.is_global or address.is_multicast
            or address in ipaddress.ip_network('192.88.99.0/24')):
        raise ValueError
    return str(address)


def probe(interface, *, deadline=None):
    # Deliberately do not inherit proxies, curl CA overrides, SSL key logging,
    # or other curl environment configuration. --disable must be first.
    env = {'PATH': os.environ.get('PATH', os.defpath), 'LC_ALL': 'C'}
    args = ['curl', '--disable', '--noproxy', '*', '--interface', interface,
            '-4', '--proto', '=https', '--connect-timeout', '5', '--max-time', '15',
            '--max-filesize', '4096', '-fsS', ENDPOINT]
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    except OSError:
        raise Unknown('curl unavailable; install curl and retry.') from None
    assert proc.stdout is not None  # stdout=PIPE above
    data = bytearray()
    deadline = min(deadline, time.monotonic() + 20) if deadline is not None else time.monotonic() + 20
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise Unknown('curl timed out; retry after checking the VPN.')
                chunk = os.read(proc.stdout.fileno(), 4097 - len(data))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > 4096:
                    raise Unknown('curl response was too large; retry later.')
        if proc.wait(timeout=max(0.01, deadline - time.monotonic())) != 0:
            raise Unknown('curl failed; check VPN, TLS trust, and connectivity.')
    except subprocess.TimeoutExpired:
        raise Unknown('curl timed out; retry after checking the VPN.') from None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        proc.stdout.close()
    try:
        lines = data.decode('ascii').splitlines()
        ips = [line[3:] for line in lines if line.startswith('ip=')]
        if len(ips) != 1:
            raise ValueError
        return public_ipv4(ips[0])
    except (ValueError, UnicodeError):
        raise Unknown('Probe returned an invalid or ambiguous public IPv4 address.') from None


def rotation_dir():
    # A UID's passwd home is the shared authority, never HOME or XDG overrides.
    try:
        home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    except KeyError:
        raise Unknown('Account home lookup failed; fix the passwd/NSS entry and retry.') from None
    if not home.is_absolute():
        raise Unknown('Account home is unavailable; cannot coordinate rotation.')
    directory = home / '.host-egress-rotation'
    directory.mkdir(mode=0o700, exist_ok=True)
    info = directory.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise Unknown('Rotation directory must be owner-owned and mode 0700.')
    # Persist the directory entry too; syncing only the directory does not
    # guarantee it survives a crash after first creation.
    parent_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    return directory


class ObservationFailure(Exception):
    def __init__(self, stage, code, attempts):
        super().__init__(code)
        self.stage, self.code, self.attempts = stage, code, attempts


def verify_after_switch(before, candidate, baseline):
    """Retry complete observations only; caller owns the lock and latch."""
    import egress_switch
    deadline = time.monotonic() + POST_SWITCH_TIMEOUT
    original_run = egress_inspect.run
    def bounded_run(*args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 'failed', None
        return original_run(*args, timeout=min(5, remaining))
    egress_inspect.run = bounded_run
    try:
        for attempt in range(1, POST_SWITCH_ATTEMPTS + 1):
            stage, code = 'local_verification', 'observation_invalid'
            try:
                after = snapshot()
                if after[0] != before[0]:
                    raise Unknown('manager changed')
                egress_switch.verify(after, candidate)
                if snapshot() != after or time.monotonic() >= deadline:
                    raise Unknown('snapshot changed or deadline exceeded')
                stage, code = 'host_probe', 'probe_failed'
                new_ip = probe(after[2]['interface'], deadline=deadline)
                stage, code = 'local_verification', 'observation_invalid'
                if snapshot() != after:
                    raise Unknown('snapshot changed')
                egress_switch.verify(after, candidate)
                if snapshot() != after or time.monotonic() >= deadline:
                    raise Unknown('snapshot changed or deadline exceeded')
                if new_ip == baseline:
                    stage, code = 'stale_ip', 'address_unchanged'
                    raise Unknown('address unchanged')
                return attempt
            except (Unknown, egress_switch.Invalid, ValueError, KeyError, TypeError) as exc:
                if attempt == POST_SWITCH_ATTEMPTS or time.monotonic() >= deadline:
                    raise ObservationFailure(stage, code, attempt) from exc
                time.sleep(min(POST_SWITCH_RETRY_DELAY, max(0, deadline - time.monotonic())))
            except Exception as exc:
                raise ObservationFailure(stage, 'unexpected_error', attempt) from exc
        raise AssertionError('unreachable')
    finally:
        egress_inspect.run = original_run


def perform_refresh(directory, baseline, before):
    import egress_switch
    marker_created = False
    switch_invoked = False
    stage, error, attempts = 'manager_command', 'command_failed', 0
    marker = directory / 'rotation-incomplete'
    try:
        old, candidate = egress_switch.selection(before)
        # Selection commands are non-atomic; re-sample and re-list immediately
        # before the durable intent and switch, while still holding the lock.
        fresh = snapshot()
        if fresh != before or probe(fresh[2]['interface']) != baseline or snapshot() != fresh:
            raise Unknown('Manager, route or baseline changed during selection; retry.')
        if egress_switch.selection(fresh) != (old, candidate) or snapshot() != fresh:
            raise Unknown('Manager or live-listed exit changed during selection; retry.')
        fd = private_file(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        marker_created = True
        with os.fdopen(fd, 'w', encoding='ascii') as out:
            out.write('Switch may be incomplete; independent operator recovery required.\n')
            out.flush()
            os.fsync(out.fileno())
        directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
            switch_invoked = True
            egress_switch.switch(before[0], candidate)
            stage, error = 'local_verification', 'unexpected_error'
            attempts = verify_after_switch(before, candidate, baseline)
            stage, error = 'latch_storage', 'storage_failed'
            # The CLI exited and all verification passed before unlink. A crash
            # after unlink cannot leave a still-running switch from this process.
            os.unlink(marker)
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return 'refreshed'
    except Exception as exc:
        if switch_invoked:
            # An error after unlink (including directory fsync/close) must not
            # silently reopen the switch path. Recreate without replacing a
            # collision; if storage fails, report that the latch is untrusted.
            try:
                if not os.path.lexists(marker):
                    fd = private_file(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                    with os.fdopen(fd, 'wb') as out:
                        out.write(b'Switch outcome uncertain; operator recovery required.\n')
                        out.flush()
                        os.fsync(out.fileno())
                    sync_directory(directory)
                reason = 'Switch may have occurred; preserve the latch and obtain operator recovery.'
            except Exception:
                reason = 'Switch may have occurred and the latch could not be secured; stop refreshes and obtain operator recovery.'
            if isinstance(exc, ObservationFailure):
                stage, error, attempts = exc.stage, exc.code, exc.attempts
            raise SwitchUncertain(reason, stage, error, attempts) from exc
        if marker_created:
            raise Unknown('No switch performed; intent latch remains and requires operator review.') from exc
        if isinstance(exc, Unknown):
            raise
        raise Unknown('Selection or local state could not be verified; no switch performed.') from exc


def publish_private(path, data):
    """Publish a complete, durable private file without replacing a collision."""
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, path, follow_symlinks=False)
        os.unlink(temporary)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def run(mode, key):
    if mode != 'refresh':
        return run_locked(mode, key, None)
    directory = rotation_dir()
    lock = private_file(directory / '.lock', os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if os.path.lexists(directory / 'rotation-incomplete'):
            raise Unknown('Previous switch outcome uncertain; operator recovery required.')
        return run_locked(mode, key, directory)
    finally:
        os.close(lock)


def run_locked(mode, key, rotation_directory):
    if not key or len(key.encode()) > 1024:
        raise Unknown('Use a nonempty, stable incident key of at most 1024 bytes.')
    directory = state_dir()
    name = hashlib.sha256(key.encode()).hexdigest() + '.baseline'
    lock = private_file(directory / '.lock', os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        baseline_path = directory / name
        incident_path = directory / (name + '.incident')
        baseline = ''
        if mode in ('capture', 'record'):
            if os.path.lexists(baseline_path) or os.path.lexists(incident_path):
                raise Unknown('Baseline already exists; compare it or use a new incident key.')
            if mode == 'record':
                publish_private(incident_path, b'incident-v1\n')
        else:
            try:
                fd = private_file(baseline_path, os.O_RDONLY)
            except FileNotFoundError:
                if os.path.lexists(incident_path):
                    raise Unknown('Incident exists but its original baseline is unknown; use a new incident key if needed.') from None
                raise Unknown('No baseline for this key; capture once first.') from None
            # IPv4 is at most 15 bytes plus newline; one extra byte detects
            # overlong files instead of validating a truncated prefix.
            with os.fdopen(fd, 'rb') as source:
                data = source.read(17)
                try:
                    baseline = public_ipv4(data[:-1].decode('ascii'))
                    if data != (baseline + '\n').encode('ascii'):
                        raise ValueError
                except (ValueError, UnicodeError):
                    raise Unknown('Baseline is invalid; preserve it and use a new incident key.') from None
                # A prior publisher may have failed after linking the file but
                # before syncing the directory. Re-establish durability under
                # the state lock before accepting it or making observations.
                os.fsync(source.fileno())
                sync_directory(directory)
        try:
            before = snapshot()
            try:
                current = probe(before[2]['interface'])
            finally:
                after = snapshot()
            if before != after:
                raise Unknown('VPN manager, relay, or destination route changed during probe; retry.')
            if mode in ('capture', 'record'):
                publish_private(baseline_path, (current + '\n').encode('ascii'))
        except Exception as exc:
            if mode == 'record':
                reason = str(exc) if isinstance(exc, Unknown) else 'Local observation or state publication failed; inspect private state.'
                raise IncidentRecorded(reason) from exc
            raise
        if mode in ('capture', 'record'):
            return 'captured'
        if mode == 'refresh':
            if baseline != current:
                return 'already_refreshed'
            return perform_refresh(rotation_directory, baseline, before)
        return 'same' if baseline == current else 'different'
    finally:
        os.close(lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('record', 'check', 'refresh', 'capture', 'compare'))
    parser.add_argument('incident_key', help='opaque stable key for this incident; never an IP address')
    args = parser.parse_args()
    mode = {'check': 'compare'}.get(args.mode, args.mode)
    receipt = {'path': 'host-direct', 'action': 'none'}
    # This CLI is single-threaded. Set before any creation so locks and
    # directories are never briefly published with an unusable masked mode.
    old_umask = os.umask(0o077)
    try:
        receipt['result'] = run(mode, args.incident_key)
        if receipt['result'] == 'refreshed':
            receipt['action'] = 'switch'
        code = 0
    except IncidentRecorded as exc:
        receipt.update(result='incident_recorded_baseline_unknown', reason=str(exc))
        code = 1
    except SwitchUncertain as exc:
        receipt.update(result='unknown', action='switch_uncertain', reason=str(exc),
                       stage=exc.stage, error_code=exc.error, attempts=exc.attempts)
        code = 1
    except Unknown as exc:
        receipt.update(result='unknown', reason=str(exc))
        code = 1
    except (OSError, UnicodeError, ValueError):
        receipt.update(result='unknown', reason='Local state or observation failed; check private state and retry.')
        code = 1
    finally:
        os.umask(old_umask)
    print(json.dumps(receipt))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
