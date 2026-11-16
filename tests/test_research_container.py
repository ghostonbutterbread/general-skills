import importlib.util
import json
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / 'skills/safe-fetch/scripts/research_container.py'
spec = importlib.util.spec_from_file_location('research_container', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Context:
    def register_tool(self, **kwargs):
        self.registered = kwargs
        return 'registered'


class UnitTests(unittest.TestCase):
    def test_plugin_denies_without_adapter_and_never_executes(self):
        ctx = Context()
        self.assertEqual(m.register_tool(ctx), 'registered')
        with mock.patch.object(m.ResearchContainer, 'execute', side_effect=AssertionError):
            result = json.loads(ctx.registered['handler']({'command': 'true'}, task_id='x'))
        self.assertEqual(result['error'], 'exact_child_allowlist_not_verified')
        self.assertEqual(ctx.registered['name'], m.TOOL_NAME)

    def test_runtime_identity_is_resolved_not_model_argument(self):
        ctx, task = Context(), m.ResearchContainer()
        m.register_tool(ctx, lambda kw: task if kw.get('task_id') == 'approved' else None)
        with mock.patch.object(task, 'execute', return_value={'ok': True}) as execute:
            self.assertFalse(json.loads(ctx.registered['handler']({'command': 'true', 'task_id': 'approved'}, task_id='other'))['ok'])
            self.assertTrue(json.loads(ctx.registered['handler']({'command': 'true'}, task_id='approved'))['ok'])
            execute.assert_called_once()

    def test_failed_start_and_uncertain_cleanup(self):
        task = m.ResearchContainer()
        with mock.patch.object(m, '_docker', side_effect=[(None, '', False), (0, '', False), (0, '', False)]):
            self.assertFalse(task.start()['ok'])
            self.assertEqual(task.execute('true')['error'], 'container_not_running')
            receipt = task.close()
            self.assertEqual(receipt['cleanup'], 'absent_at_check_delayed_operation_possible')
            self.assertEqual(task.close(), receipt)

    def test_exec_client_timeout_disallows_reuse(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_docker', return_value=(None, '', False)):
            self.assertTrue(task.execute('true')['cleanup_required'])
            self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_invalid_inputs_do_not_call_docker(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_docker', side_effect=AssertionError):
            for command, timeout in [('', 2), ('a\x00b', 2), ('x', True), ('x', 61)]:
                self.assertFalse(task.execute(command, timeout)['ok'])


@unittest.skipUnless(os.environ.get('RESEARCH_DOCKER_TEST') == '1', 'explicit real Docker test')
class DockerTests(unittest.TestCase):
    def test_real_lifecycle_reuse_isolation_failures_and_timeout(self):
        task = m.ResearchContainer()
        with tempfile.TemporaryDirectory(prefix='research-host-sentinel-') as directory:
            sentinel = Path(directory) / 'sentinel'
            sentinel.write_text('host-only-value')
            try:
                with mock.patch.dict(os.environ, {'RESEARCH_PRIVATE_SENTINEL': 'host-only-value'}):
                    start = task.start()
                print('start:', start, flush=True)
                self.assertTrue(start['ok'], start)
                command = "test ! -e %s && test -z \"${RESEARCH_PRIVATE_SENTINEL+x}\" && test $(id -u) = 65534 && test ! -S /var/run/docker.sock && printf fixture > /tmp/fixture && printf first" % shlex.quote(str(sentinel))
                ctx = Context()
                m.register_tool(ctx, lambda kw: task if kw.get('session_id') == 'fixture-child' else None)
                call = lambda command: json.loads(ctx.registered['handler']({'command': command}, session_id='fixture-child'))
                first = call(command)
                print('isolation:', first, flush=True)
                self.assertTrue(first['ok'], first)
                self.assertEqual(first['output'], 'first')
                second = call('cat /tmp/fixture; printf "\\n"; ls /sys/class/net')
                print('reuse:', second, flush=True)
                self.assertEqual(second['output'].strip(), 'fixture\nlo')
                failure = task.execute('exit 7')
                print('failure:', failure, flush=True)
                self.assertEqual(failure['exit_code'], 7)
                large = task.execute("python -c 'print(\"x\" * 100000)'")
                self.assertTrue(large['truncated'])
                self.assertLessEqual(len(large['output']), m.MAX_OUTPUT)
                timeout = task.execute('sleep 10', 1)
                print('timeout:', timeout, flush=True)
                self.assertTrue(timeout['timed_out'])
                self.assertEqual(task.execute('true')['error'], 'container_not_running')
                self.assertNotIn('fixture', str(task.receipt()))
            finally:
                receipt = task.close()
                print('cleanup:', receipt, flush=True)
                self.assertIn(receipt['cleanup'], ('absent_at_check', 'absent_at_check_delayed_operation_possible'))
                self.assertEqual(sentinel.read_text(), 'host-only-value')


if __name__ == '__main__':
    unittest.main()
