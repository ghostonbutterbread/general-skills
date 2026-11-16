import importlib.util
import json
import os
from pathlib import Path
import socket
import socketserver
import struct
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / 'skills/safe-fetch/scripts/research_container.py'
spec = importlib.util.spec_from_file_location('research_engine_transport', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Engine(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    def __init__(self, path):
        self.requests = []
        self.code = 0
        self.payload = struct.pack('>BxxxI', 1, 5) + b'hello'
        self.inspect = None
        self.failure = None
        self.delay = 0
        self.override_status = None
        self.chunked = False
        self.trickle = False
        self.slow_headers: str | None = None
        self.slow_chunk_header = False
        super().__init__(path, Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass  # expected when the client cuts off a response
    def log_message(self, *args):
        pass
    def respond(self, code, data, content_type='application/json'):
        self.send_response(self.server.override_status or code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def handle_request(self):
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.server.requests.append((self.command, self.path, data))
        if self.server.slow_headers == self.path:
            try:
                self.wfile.write(b'HTTP/1.1 200 OK\r\nX-Slow: ')
                self.wfile.flush()
                for _ in range(40):
                    self.wfile.write(b'x')
                    self.wfile.flush()
                    time.sleep(0.1)
                self.wfile.write(b'\r\nContent-Length: 0\r\n\r\n')
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if self.server.failure == self.path:
            return self.respond(500, b'{"message":"private daemon error"}')
        if self.path == '/version':
            return self.respond(200, b'{"ApiVersion":"1.44"}')
        if self.path.endswith('/exec'):
            return self.respond(201, b'{"Id":"exec-id"}')
        if self.path.endswith('/start'):
            time.sleep(self.server.delay)
            if self.server.slow_chunk_header:
                self.send_response(200)
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()
                try:
                    self.wfile.write(b'1' + b';')
                    self.wfile.flush()
                    for _ in range(40):
                        self.wfile.write(b'x')
                        self.wfile.flush()
                        time.sleep(0.1)
                    self.wfile.write(b'\r\nx\r\n0\r\n\r\n')
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.server.trickle:
                self.send_response(200)
                self.send_header('Content-Length', '28')
                self.end_headers()
                self.wfile.write(struct.pack('>BxxxI', 1, 20))
                try:
                    for _ in range(20):
                        self.wfile.write(b'x')
                        self.wfile.flush()
                        time.sleep(0.2)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.server.chunked:
                data = self.server.payload
                self.send_response(200)
                self.send_header('Transfer-Encoding', 'chunked')
                self.send_header('Content-Type', 'application/vnd.docker.raw-stream')
                self.end_headers()
                for byte in data:
                    self.wfile.write(b'1\r\n' + bytes([byte]) + b'\r\n')
                self.wfile.write(b'0\r\n\r\n')
                return
            try:
                return self.respond(200, self.server.payload, 'application/vnd.docker.raw-stream')
            except (BrokenPipeError, ConnectionResetError):
                return
        if self.path.endswith('/json'):
            result = self.server.inspect if self.server.inspect is not None else {'Running': False, 'ExitCode': self.server.code}
            return self.respond(200, json.dumps(result).encode())
        self.respond(404, b'{}')
    do_POST = handle_request
    do_GET = handle_request


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.socket = str(Path(self.directory.name) / 'docker.sock')
        self.engine = Engine(self.socket)
        self.thread = threading.Thread(target=self.engine.serve_forever, daemon=True)
        self.thread.start()
        self.env = mock.patch.dict(os.environ, {'DOCKER_HOST': 'unix://' + self.socket, 'DOCKER_CONFIG': self.directory.name}, clear=True)
        self.env.start()
        self.task = m.ResearchContainer()
        self.task.state = 'running'

    def tearDown(self):
        self.env.stop()
        self.engine.shutdown()
        self.engine.server_close()
        self.thread.join()
        self.directory.cleanup()

    def test_verified_status_from_engine_allows_reuse(self):
        for code in (0, 1, 7, 124):
            self.engine.code = code
            result = self.task.execute('exit ' + str(code))
            self.assertEqual(result['exit_code'], code)
            self.assertEqual(result['output'], 'hello')
            self.assertEqual(self.task.state, 'running')
        paths = [item[1] for item in self.engine.requests]
        self.assertEqual(paths.count('/v1.44/exec/exec-id/json'), 4)
        create = next(item for item in self.engine.requests if item[1].endswith('/exec'))
        self.assertEqual(json.loads(create[2])['Cmd'], ['sh', '-c', 'exit 0'])
        self.assertNotIn('hello', str(self.task.receipt()))

    def test_chunked_multiplex_frames(self):
        self.engine.chunked = True
        result = self.task.execute('true')
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['output'], 'hello')

    def test_output_marker_cannot_override_engine_status(self):
        output = b'done:0\n'
        self.engine.payload = struct.pack('>BxxxI', 1, len(output)) + output
        self.engine.code = 7
        result = self.task.execute('exit 7')
        self.assertEqual(result['exit_code'], 7)
        self.assertEqual(result['output'], output.decode())
        self.assertEqual(self.task.state, 'running')

    def test_multiplex_cap_and_json_bound(self):
        data = b'\xff\x00' * m.MAX_OUTPUT
        self.engine.payload = (struct.pack('>BxxxI', 2, 2) + b'er' +
                               struct.pack('>BxxxI', 1, len(data)) + data)
        ctx = type('Ctx', (), {'register_tool': lambda self, **kw: kw})()
        handler = m.register_tool(ctx, lambda _: self.task)['handler']
        response = handler({'command': 'true'})
        result = json.loads(response)
        self.assertEqual(result['exit_code'], 0)
        self.assertTrue(result['truncated'])
        self.assertTrue(result['output'].startswith('er'))
        self.assertLessEqual(len(response.encode()), m.MAX_OUTPUT)
        self.assertNotIn('output', self.task.receipt())

    def test_malformed_frames_and_status_fail_closed(self):
        for payload, status in [(b'bad', None), (struct.pack('>BxxxI', 1, 5) + b'x', None),
                                (b'', {'Running': True, 'ExitCode': 0}),
                                (b'', {'Running': False, 'ExitCode': None}),
                                (b'', {'Running': False, 'ExitCode': True})]:
            with self.subTest(payload=payload, status=status):
                self.task.state = 'running'
                self.engine.payload, self.engine.inspect = payload, status
                result = self.task.execute('true')
                self.assertTrue(result['cleanup_required'])
                self.assertEqual(self.task.state, 'uncertain')
                self.assertNotIn('output', result)

    def test_daemon_failure_at_each_phase_fails_closed(self):
        for route in ('/version', '/v1.44/containers/' + self.task.name + '/exec',
                      '/v1.44/exec/exec-id/start', '/v1.44/exec/exec-id/json'):
            with self.subTest(route=route):
                self.task.state = 'running'
                self.engine.failure = route
                result = self.task.execute('true')
                self.assertTrue(result['cleanup_required'])
                self.assertNotIn('private', str(result))
                self.assertEqual(self.task.state, 'uncertain')

    def test_unexpected_success_http_status_is_unverified(self):
        self.engine.override_status = 201
        result = self.task.execute('true')
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(self.task.state, 'uncertain')

    def test_trickling_frame_does_not_extend_command_deadline(self):
        self.engine.trickle = True
        started = time.monotonic()
        finished = threading.Event()
        def docker(args, *rest):
            if args[0] == 'ps':
                finished.set()
            return 0, '', False
        with mock.patch.object(m, '_docker', side_effect=docker):
            result = self.task.execute('true', 1)
            elapsed = time.monotonic() - started
            self.assertTrue(finished.wait(1))
        self.assertTrue(result['cleanup_required'])
        self.assertEqual(result['error'], 'command_timed_out')
        self.assertLess(elapsed, 3.2)

    def test_engine_timer_start_failure_is_transport_failure_and_releases_lock(self):
        timer_class = threading.Timer
        timers = []
        def timer_factory(*args, **kwargs):
            if timers:
                raise RuntimeError('timer unavailable')
            timer = timer_class(*args, **kwargs)
            timers.append(timer)
            return timer
        with mock.patch.object(m.threading, 'Timer', side_effect=timer_factory), mock.patch.object(m, '_docker') as docker:
            result = self.task.execute('true', 1)
            timers[0].join(1)
            docker.assert_not_called()
        self.assertFalse(timers[0].is_alive())
        self.assertEqual(result['error'], 'docker_exec_completion_unverified')
        self.assertTrue(result['cleanup_required'])
        self.assertFalse(self.task.inflight)
        self.assertTrue(self.task.exec_lock.acquire(blocking=False))
        self.task.exec_lock.release()

    def test_slow_connect_and_headers_share_one_deadline(self):
        self.engine.slow_headers = '/version'
        connect = socket.socket.connect
        def delayed_connect(sock, address):
            time.sleep(0.8)
            return connect(sock, address)
        started = time.monotonic()
        with mock.patch.object(socket.socket, 'connect', delayed_connect):
            with self.assertRaises(TimeoutError):
                m._engine_exec(self.socket, self.task.name, 'true', 1)
        elapsed = time.monotonic() - started
        self.assertGreater(elapsed, 1.7)
        self.assertLess(elapsed, 3.0)

    def test_trickling_headers_and_chunk_metadata_are_interrupted(self):
        for phase in ('version', 'start', 'chunk'):
            with self.subTest(phase=phase):
                self.task = m.ResearchContainer()
                self.task.state = 'running'
                self.engine.slow_headers = {'version': '/version',
                    'start': '/v1.44/exec/exec-id/start'}.get(phase)
                self.engine.slow_chunk_header = phase == 'chunk'
                started = time.monotonic()
                timers = []
                timer_class = threading.Timer
                def timer_factory(*args, **kwargs):
                    timer = timer_class(*args, **kwargs)
                    timers.append(timer)
                    return timer
                with mock.patch.object(m.threading, 'Timer', side_effect=timer_factory), mock.patch.object(m, '_docker', return_value=(0, '', False)) as docker:
                    result = self.task.execute('true', 1)
                    elapsed = time.monotonic() - started
                    for timer in timers:
                        timer.join(1)
                    self.assertFalse(any(timer.is_alive() for timer in timers))
                    self.assertEqual(docker.call_count, 2)
                self.assertLess(elapsed, 3.2, (phase, elapsed, result))
                self.assertEqual(result['error'], 'command_timed_out')
                self.assertTrue(result['cleanup_required'])
                self.assertEqual(self.task.state, 'uncertain')
                self.assertFalse(self.task.inflight)
                self.assertTrue(self.task.exec_lock.acquire(blocking=False))
                self.task.exec_lock.release()
                self.assertEqual(self.task.execute('true')['error'], 'container_not_running')

    def test_socket_deadline_winning_watchdog_race_still_requests_cleanup(self):
        self.engine.slow_headers = '/version'
        gate = threading.Event()
        entered = threading.Event()
        timer_class = threading.Timer
        timers = []
        def timer_factory(interval, callback):
            if not timers:
                original = callback
                def delayed_callback():
                    entered.set()
                    gate.wait(3)
                    original()
                callback = delayed_callback
            timer = timer_class(interval, callback)
            timers.append(timer)
            return timer
        try:
            with mock.patch.object(m.threading, 'Timer', side_effect=timer_factory), mock.patch.object(m, '_docker', return_value=(None, '', False)) as docker:
                result = self.task.execute('true', 1)
                self.assertEqual(result['error'], 'command_timed_out')
                self.assertTrue(entered.wait(1))
                self.assertEqual(docker.call_count, 0)
                gate.set()
                for timer in timers:
                    timer.join(1)
                self.assertFalse(any(timer.is_alive() for timer in timers))
                self.assertEqual(docker.call_count, 2)
                self.assertEqual(self.task.state, 'uncertain')
                docker.return_value = (0, '', False)
                self.assertEqual(self.task.close()['cleanup'], 'absent_at_check_delayed_operation_possible')
                self.assertEqual(docker.call_count, 4)
        finally:
            gate.set()

    def test_timeout_closes_task_and_rejects_reuse(self):
        self.engine.delay = 3
        finished = threading.Event()
        def docker(args, *rest):
            if args[0] == 'ps':
                finished.set()
            return 0, '', False
        with mock.patch.object(m, '_docker', side_effect=docker):
            result = self.task.execute('true', 1)
            self.assertTrue(finished.wait(1))
        self.assertTrue(result['cleanup_required'])
        self.assertNotEqual(self.task.state, 'running')
        self.assertEqual(self.task.execute('true')['error'], 'container_not_running')

    def test_changed_daemon_never_executes_or_cleans_other_daemon(self):
        self.task.socket_path = self.socket
        with mock.patch.dict(os.environ, {'DOCKER_HOST': 'unix:///different.sock'}), mock.patch.object(m, '_docker') as cli:
            self.assertTrue(self.task.execute('true')['cleanup_required'])
            self.assertEqual(self.task.close()['cleanup'], 'unverified')
            cli.assert_not_called()

    def test_unsupported_start_then_close_never_touches_any_daemon(self):
        with mock.patch.dict(os.environ, {'DOCKER_HOST': 'tcp://remote:2375'}), mock.patch.object(m, '_docker') as cli:
            task = m.ResearchContainer()
            self.assertEqual(task.start()['error'], 'unsupported_docker_daemon')
            task.close()
            cli.assert_not_called()

    def test_remote_named_and_tls_selection_are_rejected_before_start(self):
        for setting in ({'DOCKER_HOST': 'tcp://remote:2375'}, {'DOCKER_CONTEXT': 'remote'},
                        {'DOCKER_TLS_VERIFY': '1'},
                        {'DOCKER_HOST': 'unix:///tmp/escaped%20socket'},
                        {'DOCKER_CONTEXT': 'default', 'DOCKER_HOST': 'unix:///another.sock'}):
            with self.subTest(setting=setting), mock.patch.dict(os.environ, setting), mock.patch.object(m, '_docker') as cli:
                result = m.ResearchContainer().start()
                self.assertEqual(result['error'], 'unsupported_docker_daemon')
                cli.assert_not_called()
