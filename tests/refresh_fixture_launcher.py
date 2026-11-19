"""Fixture launcher: require seccomp before redirecting private state or faults."""
import errno
import os
from pathlib import Path
import socket
import sys

try:
    socket.socket()
except OSError as exc:
    if exc.errno != errno.EPERM:
        raise
else:
    raise SystemExit('refusing to inject without inherited socket denial')

root = Path(sys.argv[1]).resolve()
assert root.is_relative_to(Path(os.environ['TMPDIR']).resolve())
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/script-manager/scripts'))
import egress_snapshot
if sys.argv[2] not in ('production', 'post-exception', 'pre-exception', 'baseline-failure',
                        'pre-sync', 'post-sync', 'missing-nss', 'mkdir-pause', 'sync-audit',
                        'baseline-dirsync-fail', 'read-file-fail', 'read-dir-fail',
                        'ancestor-sync-fail'):
    raise SystemExit('invalid fixture launcher mode')
# Redirect the passwd lookup (not HOME/XDG) into the task-owned fixture.
from types import SimpleNamespace
if sys.argv[2] == 'missing-nss':
    def missing(uid):
        raise KeyError('missing uid')
    egress_snapshot.pwd.getpwuid = missing
else:
    egress_snapshot.pwd.getpwuid = lambda uid: SimpleNamespace(pw_dir=str(root))
if sys.argv[2] in ('post-exception', 'pre-exception'):
    import egress_switch
    def explode(*args, **kwargs):
        raise RuntimeError('private canary')
    if sys.argv[2] == 'post-exception':
        egress_switch.verify = explode
    else:
        egress_switch.selection = explode
if sys.argv[2] == 'baseline-failure':
    publish = egress_snapshot.publish_private
    def fail_baseline(path, data):
        if path.name.endswith('.baseline'):
            fsync = os.fsync
            def fail(fd):
                raise OSError('injected fsync failure')
            os.fsync = fail
            try:
                return publish(path, data)
            finally:
                os.fsync = fsync
        return publish(path, data)
    egress_snapshot.publish_private = fail_baseline
if sys.argv[2] in ('pre-sync', 'post-sync'):
    fsync = os.fsync
    kind = sys.argv[2]
    fired = False
    def fail_once(fd):
        global fired
        directory = root / '.host-egress-rotation'
        is_rotation = os.readlink('/proc/self/fd/' + str(fd)) == str(directory)
        started = (root / 'switch-started').exists()
        if not fired and is_rotation and (started == (kind == 'post-sync')):
            fired = True
            raise OSError('injected sync failure')
        return fsync(fd)
    os.fsync = fail_once
if sys.argv[2] in ('mkdir-pause', 'sync-audit', 'baseline-dirsync-fail',
                    'read-file-fail', 'read-dir-fail', 'ancestor-sync-fail'):
    kind = sys.argv[2]
    fsync = os.fsync
    def observed_sync(fd):
        path = Path(os.readlink('/proc/self/fd/' + str(fd)))
        directory = root / 'state/host-egress-snapshot'
        if ((kind == 'ancestor-sync-fail' and path == root)
                or (kind == 'baseline-dirsync-fail' and path == directory
                    and list(directory.glob('*.baseline')))
                or (kind == 'read-file-fail' and path.name.endswith('.baseline'))
                or (kind == 'read-dir-fail' and path == directory
                    and list(directory.glob('*.baseline')))):
            raise OSError('injected durability failure')
        fsync(fd)
        if kind == 'sync-audit':
            with (root / 'sync-audit').open('a') as out:
                out.write(str(path) + '\n')
    os.fsync = observed_sync
    if kind == 'mkdir-pause':
        mkdir = Path.mkdir
        def pause_after_mkdir(self, mode=0o777, parents=False, exist_ok=False):
            result = mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)
            if self == Path(os.environ['XDG_STATE_HOME']):
                os.write(int(os.environ['READY_FD']), b'R')
                if os.read(int(os.environ['RELEASE_FD']), 1) != b'R':
                    raise RuntimeError('controller closed release pipe')
            return result
        Path.mkdir = pause_after_mkdir
sys.argv = ['egress_snapshot.py', *sys.argv[3:]]
(root / ('launcher-ready-' + sys.argv[2])).touch()
raise SystemExit(egress_snapshot.main())
