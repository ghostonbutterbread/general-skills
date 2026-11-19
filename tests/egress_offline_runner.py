"""Run egress CLI fixtures with an inherited Linux seccomp network denial.

Set TMPDIR to an owner-private scratch directory before running this script.
"""
import ctypes
import ctypes.util
import errno
import os
import socket
import sys
import tempfile

root = tempfile.mkdtemp(prefix='egress-fixtures-', dir=os.environ['TMPDIR'])
lib = ctypes.CDLL(ctypes.util.find_library('seccomp'), use_errno=True)
lib.seccomp_init.argtypes = [ctypes.c_uint32]
lib.seccomp_init.restype = ctypes.c_void_p
lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
lib.seccomp_rule_add.restype = ctypes.c_int
lib.seccomp_load.argtypes = [ctypes.c_void_p]
lib.seccomp_load.restype = ctypes.c_int
ctx = lib.seccomp_init(0x7fff0000)
if not ctx:
    raise SystemExit('seccomp init failed')
for name in (b'socket', b'socketpair', b'connect'):
    nr = lib.seccomp_syscall_resolve_name(name)
    if nr < 0 or lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, nr, 0) != 0:
        raise SystemExit('seccomp rule failed')
if lib.seccomp_load(ctx) != 0:
    raise SystemExit('seccomp load failed')
try:
    socket.socket()
except PermissionError:
    pass
else:
    raise SystemExit('network fence failed')
env = {'HOME': root, 'TMPDIR': root, 'XDG_STATE_HOME': root + '/state',
       'XDG_CONFIG_HOME': root + '/config', 'XDG_CACHE_HOME': root + '/cache',
       'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1',
       'PYTHONNOUSERSITE': '1', 'LC_ALL': 'C.UTF-8'}
os.execve(sys.executable, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                           '-p', 'test_egress*.py', '-v'], env)
