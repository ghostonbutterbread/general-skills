#!/usr/bin/env python3
"""Offline protocol fixture; never contacts Docker or the network."""
import importlib.util
import json
import os
import signal
import sys
import time


def terminated(_signum, _frame):
    with open(os.environ['OMP_TEST_LOG'], 'a', encoding='utf-8') as log:
        log.write('SIGTERM\n')
    os._exit(143)


signal.signal(signal.SIGTERM, terminated)


class FakeTask:
    name = 'research-task-offline-fixture'

    def call(self, op):
        with open(os.environ['OMP_TEST_LOG'], 'a', encoding='utf-8') as log:
            log.write(op + '\n')

    def start(self):
        self.call('start')
        return {'ok': True, 'container': self.name}

    def execute(self, command, timeout):
        self.call('execute')
        time.sleep(float(os.environ.get('OMP_TEST_EXEC_DELAY', '0')))
        return {'ok': True, 'output': 'untrusted fake data', 'trust': 'untrusted_container_output'}

    def close(self):
        self.call('close')
        time.sleep(float(os.environ.get('OMP_TEST_CLOSE_DELAY', '0')))
        return {'container': self.name, 'cleanup': 'unverified' if os.environ.get('OMP_TEST_BAD_CLOSE') else 'absent_at_check'}


source = os.environ.get('OMP_TEST_REAL_STDIO')
if source:
    spec = importlib.util.spec_from_file_location('shared_research_stdio', source)
    if spec is None or spec.loader is None:
        raise RuntimeError('shared stdio fixture cannot be imported')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.exit(module.serve(sys.stdin, sys.stdout, sys.stderr, FakeTask()))


def emit(op, result):
    print(json.dumps({'op': op, 'result': result}), flush=True)


task = FakeTask()
emit('ready', {'container': task.name})
for line in sys.stdin:
    req = json.loads(line)
    op = req['op']
    if op == 'start':
        emit(op, task.start())
    elif op == 'execute':
        emit(op, task.execute(req['command'], req.get('timeout', 15)))
    elif op == 'close':
        emit(op, task.close())
        break
