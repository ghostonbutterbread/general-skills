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
            self.assertEqual(task.state, 'uncertain')
        with mock.patch.object(m, '_docker', side_effect=[(0, '', False), (0, task.name, False)]) as docker:
            self.assertEqual(task.close()['cleanup'], 'unverified')
            self.assertEqual(docker.call_args_list[0].args[0], ['rm', '-f', task.name])

    def test_incomplete_container_listing_is_not_absence(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_docker', side_effect=[(0, '', False), (0, '', True)]):
            self.assertEqual(task.close()['cleanup'], 'unverified')
            self.assertEqual(task.state, 'uncertain')

    def test_exec_client_timeout_disallows_reuse(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_docker', return_value=(None, '', False)):
            self.assertTrue(task.execute('true')['cleanup_required'])
            self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_unexpected_exec_error_requires_cleanup_without_output_leak(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_docker', side_effect=RuntimeError('secret raw stdout')):
            result = task.execute('true')
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(task.state, 'uncertain')
        self.assertNotIn('secret', str(result))
        self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_wait_exception_after_client_launch_marks_uncertain(self):
        import io
        proc = mock.Mock()
        proc.stdout = io.BytesIO(b'secret raw stdout')
        proc.wait.side_effect = RuntimeError('secret raw stdout')
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m.subprocess, 'Popen', return_value=proc) as popen:
            result = task.execute('true')
        popen.assert_called_once()
        proc.kill.assert_called_once()
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(task.state, 'uncertain')
        self.assertNotIn('secret', str(result))

    def test_serialized_response_bound_with_invalid_bytes_and_escapes(self):
        import io
        proc = mock.Mock()
        proc.stdout = io.BytesIO((b'\xff' + b'\x00') * (m.MAX_OUTPUT // 2))
        proc.wait.return_value = 0
        task = m.ResearchContainer()
        task.state = 'running'
        ctx = Context()
        m.register_tool(ctx, lambda kw: task)
        with mock.patch.object(m.subprocess, 'Popen', return_value=proc):
            response = ctx.registered['handler']({'command': 'true'})
        self.assertLessEqual(len(response.encode('utf-8')), m.MAX_OUTPUT)
        self.assertTrue(json.loads(response)['truncated'])

    def test_incomplete_drain_marks_output_truncated(self):
        proc = mock.Mock()
        proc.stdout = mock.Mock()
        proc.wait.return_value = 0
        reader = mock.Mock()
        reader.is_alive.return_value = True
        with mock.patch.object(m.subprocess, 'Popen', return_value=proc), mock.patch.object(
                m.threading, 'Thread', return_value=reader):
            _, _, truncated = m._docker(['exec'], 1)
        self.assertTrue(truncated)

    def test_timeout_exit_codes_are_ambiguous(self):
        for code in (124, 137):
            task = m.ResearchContainer()
            task.state = 'running'
            with mock.patch.object(m, '_docker', return_value=(code, '', False)):
                result = task.execute('exit ' + str(code))
            self.assertIsNone(result['timed_out'])
            self.assertTrue(result['cleanup_required'])

    def test_task_expiry_removes_only_owned_container_and_prevents_reuse(self):
        task = m.ResearchContainer()
        with mock.patch.object(m.threading, 'Timer') as timer, mock.patch.object(
                m, '_docker', side_effect=[(0, '', False), (0, '', False), (0, '', False)]) as docker:
            self.assertTrue(task.start()['ok'])
            expiry = timer.call_args.args[1]
            self.assertEqual(timer.call_args.args[0], 900)
            expiry()
            self.assertEqual(docker.call_args_list[1].args[0], ['rm', '-f', task.name])
            self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_cancel_does_not_wait_for_inflight_exec(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        task = m.ResearchContainer()
        task.state = 'running'
        def docker(args, timeout):
            if args[0] == 'exec':
                entered.set()
                release.wait(2)
                return 0, 'untrusted', False
            return 0, '', False
        with mock.patch.object(m, '_docker', side_effect=docker):
            worker = threading.Thread(target=task.execute, args=('true',))
            worker.start()
            self.assertTrue(entered.wait(1))
            closer = threading.Thread(target=task.close)
            closer.start()
            closer.join(0.5)
            finished = not closer.is_alive()
            release.set()
            worker.join(2)
            closer.join(2)
        self.assertTrue(finished, 'cleanup blocked behind the running exec')
        self.assertNotEqual(task.state, 'running')

    def test_cancel_during_start_reconciles_after_late_create(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        task = m.ResearchContainer()
        calls = []
        def docker(args, timeout):
            calls.append(args)
            if args[0] == 'run':
                entered.set()
                release.wait(2)
            return 0, '', False
        with mock.patch.object(m.threading, 'Timer'), mock.patch.object(m, '_docker', side_effect=docker):
            result = []
            worker = threading.Thread(target=lambda: result.append(task.start()))
            worker.start()
            self.assertTrue(entered.wait(1))
            self.assertEqual(task.close()['cleanup'], 'absent_at_check_delayed_operation_possible')
            release.set()
            worker.join(2)
        self.assertFalse(result[0]['ok'])
        self.assertEqual(sum(c == ['rm', '-f', task.name] for c in calls), 2)
        self.assertEqual(task.state, 'uncertain')

    def test_host_command_deadline_closes_container_on_hung_exec(self):
        import threading
        entered, release = threading.Event(), threading.Event()
        task = m.ResearchContainer()
        task.state = 'running'
        def docker(args, timeout):
            if args[0] == 'exec':
                entered.set()
                release.wait(2)
                return 0, 'private', False
            return 0, '', False
        with mock.patch.object(m.threading, 'Timer') as timer, mock.patch.object(m, '_docker', side_effect=docker):
            results = []
            worker = threading.Thread(target=lambda: results.append(task.execute('true', 3)))
            worker.start()
            self.assertTrue(entered.wait(1))
            self.assertEqual(timer.call_args.args[0], 4)
            timer.call_args.args[1]()
            release.set()
            worker.join(2)
        self.assertEqual(results[0]['error'], 'task_cancelled')
        self.assertNotIn('private', str(results))
        self.assertEqual(task.state, 'uncertain')

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
                if timeout.get('error') == 'timeout_or_command_exit_ambiguous':
                    self.assertIsNone(timeout['timed_out'])
                else:
                    self.assertEqual(timeout.get('error'), 'task_cancelled')
                self.assertTrue(timeout['cleanup_required'])
                self.assertEqual(task.execute('true')['error'], 'container_not_running')
                self.assertNotIn('fixture', str(task.receipt()))
            finally:
                receipt = task.close()
                print('cleanup:', receipt, flush=True)
                self.assertIn(receipt['cleanup'], ('absent_at_check', 'absent_at_check_delayed_operation_possible'))
                self.assertEqual(sentinel.read_text(), 'host-only-value')


if __name__ == '__main__':
    unittest.main()
