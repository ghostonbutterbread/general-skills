#!/usr/bin/env python3
"""Run the OMP SDK fixture with isolated HOME and network syscalls denied."""
import ctypes
import ctypes.util
import errno
import os
import socket
import subprocess
import sys

root = os.path.abspath(sys.argv[1])
omp = os.path.abspath(sys.argv[2])
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
    raise RuntimeError('seccomp_init failed')
for name in (b'socket', b'connect'):
    nr = lib.seccomp_syscall_resolve_name(name)
    if nr < 0 or lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, nr, 0):
        raise RuntimeError('seccomp rule failed')
if lib.seccomp_load(ctx):
    raise RuntimeError('seccomp_load failed')
try:
    socket.socket()
    raise RuntimeError('network block failed')
except OSError as exc:
    if exc.errno != errno.EPERM:
        raise
print('Network socket creation denied with EPERM')
env = {'HOME': root, 'PATH': '/usr/bin:/bin', 'XDG_CONFIG_HOME': root + '/config',
       'XDG_CACHE_HOME': root + '/cache', 'XDG_DATA_HOME': root + '/data',
       'TERM': 'dumb', 'NO_COLOR': '1'}
if len(sys.argv) > 3:
    env['OMP_TEST_CASE'] = sys.argv[3]
cmd = [omp, '--mode', 'rpc', '--offline', '--no-session', '--no-extensions', '--no-skills',
       '--no-rules', '--no-context-files', '--no-lsp', '--no-pty', '--no-title', '--extension',
       root + '/tests/fixtures/omp_research_offline.ts', '--cwd', root]
p = subprocess.run(cmd, input='', text=True, capture_output=True, env=env, cwd=root, timeout=110)
print('omp exit:', p.returncode, '(1 expected after fixture: no default model)')
print(p.stderr)
if p.returncode != 1 or 'OMP ADAPTER OFFLINE PASS' not in p.stderr:
    raise SystemExit('fixture failed')
print('offline SDK fixture: PASS')
