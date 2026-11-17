import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/safe-fetch/scripts/research_stdio.py'


def load_cli():
    spec = importlib.util.spec_from_file_location('research_stdio', SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeContainer:
    def __init__(self):
        self.name = 'research-task-fake'
        self.calls = []

    def start(self):
        self.calls.append(('start',))
        return {'ok': True, 'container': self.name, 'network': 'bridge'}

    def execute(self, command, timeout=15):
        self.calls.append(('execute', command, timeout))
        return {'ok': command != 'false', 'exit_code': 1 if command == 'false' else 0,
                'output': command, 'truncated': False, 'timed_out': False,
                'trust': 'untrusted_container_output'}

    def close(self):
        self.calls.append(('close',))
        return {'container': self.name, 'cleanup': 'absent_at_check'}


class StdioTests(unittest.TestCase):
    def test_persistent_request_flow_and_explicit_close(self):
        cli = load_cli()
        task = FakeContainer()
        requests = [dict(op='start'), dict(op='execute', command='false'),
                    dict(op='execute', command='true', timeout=8), dict(op='close')]
        out, err = io.StringIO(), io.StringIO()
        rc = cli.serve(io.StringIO(''.join(json.dumps(r) + '\n' for r in requests)), out, err, task)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(rc, 0)
        self.assertEqual([r['op'] for r in replies], ['start', 'execute', 'execute', 'close'])
        self.assertEqual(replies[1]['result']['exit_code'], 1)
        self.assertTrue(replies[2]['result']['ok'])
        self.assertEqual(task.calls, [('start',), ('execute', 'false', 15), ('execute', 'true', 8), ('close',)])
        self.assertEqual(err.getvalue(), '')

    def test_invalid_lines_do_not_prevent_later_execution(self):
        task = FakeContainer()
        out, err = io.StringIO(), io.StringIO()
        data = 'not json\n[]\n{"op":"bogus"}\n{"op":"start","bad":1}\n{"op":"start"}\n{"op":"close"}\n'
        self.assertEqual(load_cli().serve(io.StringIO(data), out, err, task), 0)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([r['result'].get('error') for r in replies[:4]],
                         ['invalid_json', 'invalid_request', 'invalid_op', 'invalid_request'])
        self.assertEqual(task.calls, [('start',), ('close',)])

    def test_eof_always_closes_and_emits_receipt_on_stderr(self):
        task = FakeContainer()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(load_cli().serve(io.StringIO('{"op":"start"}\n'), out, err, task), 0)
        self.assertEqual(task.calls, [('start',), ('close',)])
        self.assertEqual(json.loads(err.getvalue())['result']['cleanup'], 'absent_at_check')

    def test_uncertain_close_is_retryable_until_eof_and_never_claims_success(self):
        class Uncertain(FakeContainer):
            def close(self):
                self.calls.append(('close',))
                return {'container': self.name, 'cleanup': 'absent_at_check_delayed_operation_possible'}
        task = Uncertain()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(load_cli().serve(io.StringIO('{"op":"start"}\n{"op":"close"}\n'), out, err, task), 1)
        self.assertEqual(task.calls, [('start',), ('close',), ('close',)])
        self.assertEqual(json.loads(err.getvalue())['result']['cleanup'], 'absent_at_check_delayed_operation_possible')

    def test_uncertain_close_can_be_retried_in_same_process(self):
        class Retry(FakeContainer):
            def close(self):
                self.calls.append(('close',))
                return {'container': self.name, 'cleanup': 'unverified' if len(self.calls) == 2 else 'absent_at_check'}
        task = Retry()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(load_cli().serve(io.StringIO('{"op":"start"}\n{"op":"close"}\n{"op":"close"}\n'), out, err, task), 0)
        self.assertEqual([json.loads(x)['result']['cleanup'] for x in out.getvalue().splitlines()[1:]],
                         ['unverified', 'absent_at_check'])
        self.assertEqual(err.getvalue(), '')

    def test_duplicate_start_is_an_actionable_error_and_process_stays_usable(self):
        class Once(FakeContainer):
            def start(self):
                if self.calls:
                    raise RuntimeError('container already started or closed')
                return super().start()
        task = Once()
        out, err = io.StringIO(), io.StringIO()
        data = '{"op":"start"}\n{"op":"start"}\n{"op":"execute","command":"true"}\n{"op":"close"}\n'
        self.assertEqual(load_cli().serve(io.StringIO(data), out, err, task), 0)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(replies[1]['result']['error'], 'start_invalid_state')
        self.assertTrue(replies[2]['result']['ok'])

    def test_real_core_with_mocked_docker_and_engine(self):
        path = SCRIPT.with_name('research_container.py')
        spec = importlib.util.spec_from_file_location('research_container_test_core', path)
        assert spec is not None and spec.loader is not None
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        task = core.ResearchContainer()
        out, err = io.StringIO(), io.StringIO()
        data = '{"op":"start"}\n{"op":"execute","command":"false"}\n{"op":"execute","command":"true"}\n{"op":"close"}\n'
        with mock.patch.object(core, '_selected_socket', return_value='/fake.sock'), \
             mock.patch.object(core, '_docker', return_value=(0, '', False)) as docker, \
             mock.patch.object(core, '_engine_exec', side_effect=[(1, 'bad', False), (0, 'ok', False)]) as engine:
            self.assertEqual(load_cli().serve(io.StringIO(data), out, err, task), 0)
        results = [json.loads(line)['result'] for line in out.getvalue().splitlines()]
        self.assertEqual([r.get('exit_code') for r in results[1:3]], [1, 0])
        self.assertEqual(results[-1]['cleanup'], 'absent_at_check')
        self.assertEqual(engine.call_count, 2)
        self.assertEqual(docker.call_args_list[1].args[0], ['rm', '-f', task.name])

    def test_unexpected_failure_still_attempts_cleanup(self):
        class Broken(FakeContainer):
            def execute(self, command, timeout=15):
                raise OSError('private diagnostic')
        task = Broken()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(load_cli().serve(io.StringIO('{"op":"execute","command":"true"}\n'), out, err, task), 1)
        self.assertEqual(task.calls, [('close',)])
        self.assertNotIn('private diagnostic', err.getvalue())
        self.assertIn('absent_at_check', err.getvalue())

    def test_cleanup_exception_reports_exact_name_and_failure(self):
        class BrokenClose(FakeContainer):
            def close(self):
                raise OSError('daemon error')
        task = BrokenClose()
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(load_cli().serve(io.StringIO(''), out, err, task), 1)
        result = json.loads(err.getvalue())['result']
        self.assertEqual((result['container'], result['cleanup']), (task.name, 'unverified'))

    def test_subprocess_entrypoint_with_fake_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(SCRIPT, root / SCRIPT.name)
            (root / 'research_container.py').write_text('''\
class ResearchContainer:
    def __init__(self): self.name = "research-task-subprocess"
    def start(self): return {"ok": True, "container": self.name, "network": "bridge"}
    def execute(self, command, timeout=15): return {"ok": True, "output": command, "timeout": timeout}
    def close(self): return {"container": self.name, "cleanup": "absent_at_check"}
''')
            proc = subprocess.run([sys.executable, str(root / SCRIPT.name)],
                input='{"op":"start"}\n{"op":"execute","command":"hello"}\n{"op":"close"}\n',
                text=True, capture_output=True, timeout=10, env={'PATH': os.environ.get('PATH', '')})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            replies = [json.loads(x) for x in proc.stdout.splitlines()]
            self.assertEqual([x['op'] for x in replies], ['start', 'execute', 'close'])
            self.assertEqual(replies[1]['result']['output'], 'hello')
            self.assertEqual(proc.stderr, '')


if __name__ == '__main__':
    unittest.main()
