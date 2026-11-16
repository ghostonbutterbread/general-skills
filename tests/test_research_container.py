import importlib.util
import json
import os
from pathlib import Path
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
    def test_docker_uses_isolated_config_without_proxy_credentials(self):
        import io
        with tempfile.TemporaryDirectory() as home:
            host = Path(home) / 'host-config'
            host.mkdir()
            (host / 'config.json').write_text(json.dumps({'proxies': {'default': {'httpProxy': 'http://user:secret@proxy'}}}))
            proc = mock.Mock(stdout=io.BytesIO(b''))
            proc.wait.return_value = 0
            def launch(*args, **kwargs):
                isolated = Path(kwargs['env']['DOCKER_CONFIG'])
                self.assertNotEqual(isolated, host)
                config = isolated / 'config.json'
                self.assertNotIn('secret', config.read_text() if config.exists() else '')
                self.assertEqual(kwargs['env']['DOCKER_HOST'], 'unix:///task.sock')
                return proc
            with mock.patch.dict(os.environ, {'DOCKER_CONFIG': str(host), 'DOCKER_HOST': 'unix:///task.sock'}, clear=True), mock.patch.object(m.subprocess, 'Popen', side_effect=launch):
                self.assertEqual(m._docker(['run'], 1)[0], 0)

    def test_docker_rejects_named_context_instead_of_changing_daemon(self):
        with tempfile.TemporaryDirectory() as host:
            (Path(host) / 'config.json').write_text('{"currentContext":"remote"}')
            with mock.patch.dict(os.environ, {'DOCKER_CONFIG': host}, clear=True), mock.patch.object(m.subprocess, 'Popen') as launch:
                self.assertIsNone(m._docker(['ps'], 1)[0])
                launch.assert_not_called()
        with mock.patch.dict(os.environ, {'DOCKER_CONTEXT': 'remote'}, clear=True), mock.patch.object(m.subprocess, 'Popen') as launch:
            self.assertIsNone(m._docker(['ps'], 1)[0])
            launch.assert_not_called()

    def test_listing_read_failure_does_not_close_and_can_retry(self):
        import io
        class BrokenStream(io.BytesIO):
            def read(self, size=-1):
                raise OSError('read failed')
        task = m.ResearchContainer()
        task.state = 'running'
        def process(stream):
            proc = mock.Mock(stdout=stream)
            proc.wait.return_value = 0
            return proc
        with mock.patch.object(m.subprocess, 'Popen', side_effect=[process(io.BytesIO()), process(BrokenStream())]):
            self.assertEqual(task.close()['cleanup'], 'unverified')
        self.assertEqual(task.state, 'uncertain')
        with mock.patch.object(m, '_docker', return_value=(0, '', False)) as docker:
            task.close()
            self.assertEqual(docker.call_count, 2)

    def test_reader_start_failure_reaps_client(self):
        import io
        proc = mock.Mock(stdout=io.BytesIO())
        with mock.patch.object(m.subprocess, 'Popen', return_value=proc), mock.patch.object(m.threading, 'Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('thread unavailable')
            with self.assertRaises(RuntimeError):
                m._docker(['exec'], 1)
        proc.kill.assert_called_once()
        proc.wait.assert_called()

    def test_reader_start_failure_still_waits_if_kill_fails(self):
        import io
        proc = mock.Mock(stdout=io.BytesIO())
        proc.kill.side_effect = ProcessLookupError('already exited')
        with mock.patch.object(m.subprocess, 'Popen', return_value=proc), mock.patch.object(m.threading, 'Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('thread unavailable')
            with self.assertRaises(RuntimeError):
                m._docker(['exec'], 1)
        proc.wait.assert_called()

    def test_start_timer_failure_does_not_launch_or_leave_inflight(self):
        task = m.ResearchContainer()
        with mock.patch.object(m.threading, 'Timer') as timer, mock.patch.object(m, '_docker') as docker:
            timer.return_value.start.side_effect = RuntimeError('thread unavailable')
            self.assertFalse(task.start()['ok'])
            docker.assert_not_called()
        self.assertFalse(task.inflight)
        self.assertNotEqual(task.state, 'running')

    def test_exec_timer_failure_releases_busy_lock_without_launch(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m.threading, 'Timer') as timer, mock.patch.object(m, '_docker') as docker:
            timer.return_value.start.side_effect = RuntimeError('thread unavailable')
            self.assertFalse(task.execute('true')['ok'])
            docker.assert_not_called()
        self.assertFalse(task.inflight)
        self.assertIsNone(task.command_token)
        self.assertTrue(task.exec_lock.acquire(blocking=False))
        task.exec_lock.release()

    def test_daemon_failure_exit_one_never_allows_reuse(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_engine_exec', side_effect=OSError('daemon failure')):
            result = task.execute('true')
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(task.state, 'uncertain')
        self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_unreachable_daemon_requires_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            task = m.ResearchContainer()
            task.state = 'running'
            env = {'PATH': os.environ.get('PATH', ''), 'DOCKER_CONFIG': directory,
                   'DOCKER_HOST': 'unix://' + str(Path(directory) / 'missing.sock')}
            with mock.patch.dict(os.environ, env, clear=True):
                result = task.execute('true')
            self.assertEqual(result['error'], 'docker_exec_completion_unverified')
            self.assertTrue(result['cleanup_required'])
            self.assertEqual(task.state, 'uncertain')

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
        with mock.patch.object(m, '_engine_exec', side_effect=TimeoutError):
            self.assertTrue(task.execute('true')['cleanup_required'])
            self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_unexpected_exec_error_requires_cleanup_without_output_leak(self):
        task = m.ResearchContainer()
        task.state = 'running'
        with mock.patch.object(m, '_engine_exec', side_effect=RuntimeError('secret raw stdout')):
            result = task.execute('true')
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(task.state, 'uncertain')
        self.assertNotIn('secret', str(result))
        self.assertEqual(task.execute('true')['error'], 'container_not_running')

    def test_serialized_response_bound_with_invalid_bytes_and_escapes(self):
        task = m.ResearchContainer()
        task.state = 'running'
        ctx = Context()
        m.register_tool(ctx, lambda kw: task)
        with mock.patch.object(m, '_engine_exec', return_value=(0, '\ufffd\x00' * m.MAX_OUTPUT, True)):
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

    def test_engine_timeout_like_exit_codes_are_real_codes(self):
        for code in (124, 125, 137):
            task = m.ResearchContainer()
            task.state = 'running'
            with mock.patch.object(m, '_engine_exec', return_value=(code, '', False)):
                result = task.execute('exit ' + str(code))
            self.assertEqual(result['exit_code'], code)
            self.assertEqual(task.state, 'running')

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
        def engine(*args):
            entered.set()
            release.wait(2)
            return 0, 'untrusted', False
        with mock.patch.object(m, '_engine_exec', side_effect=engine), mock.patch.object(m, '_docker', return_value=(0, '', False)):
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
        def docker(args, timeout, *rest):
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
        def engine(*args):
            entered.set()
            release.wait(2)
            return 0, 'private', False
        with mock.patch.object(m.threading, 'Timer') as timer, mock.patch.object(m, '_engine_exec', side_effect=engine), mock.patch.object(m, '_docker', return_value=(0, '', False)):
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
    def test_real_foreground_reuse_and_exit_status(self):
        task = m.ResearchContainer()
        try:
            start = task.start()
            print('start:', start, flush=True)
            self.assertTrue(start['ok'], start)
            for command, code in [('true', 0), ('exit 1', 1), ('exit 7', 7), ('true', 0)]:
                result = task.execute(command)
                print('foreground result:', result, flush=True)
                self.assertEqual(result.get('exit_code'), code, result)
                self.assertEqual(task.state, 'running')
        finally:
            receipt = task.close()
            print('cleanup:', receipt, flush=True)
            self.assertEqual(receipt['cleanup'], 'absent_at_check')


if __name__ == '__main__':
    unittest.main()
