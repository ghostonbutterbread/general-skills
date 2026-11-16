"""Task-owned Docker transport; agent/provider stay on the host.

This is not a standalone authorizer. See scripts/README.md for the required
trusted lifecycle adapter and for residual container and timeout limitations.
"""
from __future__ import annotations

import http.client
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import tempfile
import threading
import time
from urllib.parse import quote
import uuid

IMAGE = "python:3.12-slim"
TOOL_NAME = "research_container"
MAX_OUTPUT = 32768
MAX_COMMAND = 8192


def _docker(args, timeout, socket_path=None):
    """Use a private CLI config and drain output to a bounded prefix.

    Named contexts live in the user's CLI config; refusing them prevents the
    isolated config from silently selecting a different daemon.
    """
    try:
        env = os.environ.copy()
        host_config = Path(env.get("DOCKER_CONFIG") or Path.home() / ".docker")
        config_file = host_config / "config.json"
        try:
            with config_file.open(encoding="utf-8") as source:
                context = json.load(source).get("currentContext")
        except FileNotFoundError:
            context = None
        if context not in (None, "", "default") or env.get("DOCKER_CONTEXT", "") not in ("", "default"):
            return None, "", False
        # Docker's default TLS certificate directory follows its config dir.
        if (env.get("DOCKER_TLS") or env.get("DOCKER_TLS_VERIFY")) and not env.get("DOCKER_CERT_PATH"):
            env["DOCKER_CERT_PATH"] = str(host_config)
    except (OSError, ValueError, AttributeError, TypeError):
        return None, "", False
    with tempfile.TemporaryDirectory(prefix="research-docker-config-") as config:
        env["DOCKER_CONFIG"] = config
        if socket_path is not None:
            env.pop("DOCKER_CONTEXT", None)  # DOCKER_CONTEXT takes precedence over DOCKER_HOST.
            env["DOCKER_HOST"] = "unix://" + socket_path
        return _docker_client(args, timeout, env)


def _docker_client(args, timeout, env):
    try:
        process = subprocess.Popen(["docker", *args], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)
    except OSError:
        return None, "", False
    chunks = bytearray()
    truncated = False
    drain_error = []
    stream = process.stdout
    assert stream is not None  # stdout=PIPE above

    def drain():
        nonlocal truncated
        try:
            while True:
                data = stream.read(8192)
                if not data:
                    break
                remaining = max(0, MAX_OUTPUT - len(chunks))
                chunks.extend(data[:remaining])
                truncated |= len(data) > remaining
        except Exception as exc:
            drain_error.append(exc)
        finally:
            try:
                stream.close()
            except Exception as exc:
                drain_error.append(exc)

    reader = None
    try:
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        rc = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        rc = None
    except Exception:
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=2)
        except Exception:
            pass
        if reader is not None and reader.ident is not None:
            reader.join(timeout=2)
        else:
            stream.close()
        raise
    reader.join(timeout=2)
    if drain_error:
        raise OSError("Docker output drain failed") from drain_error[0]
    # A Docker child holding the stream may outlive the client. Do not wait forever.
    return rc, bytes(chunks).decode("utf-8", "replace"), truncated or reader.is_alive()


def _selected_socket():
    """Resolve only the same explicit/default local daemon as the CLI."""
    env = os.environ
    config = Path(env.get('DOCKER_CONFIG') or Path.home() / '.docker') / 'config.json'
    try:
        with config.open(encoding='utf-8') as source:
            context = json.load(source).get('currentContext')
    except FileNotFoundError:
        context = None
    if context not in (None, '', 'default') or env.get('DOCKER_CONTEXT', '') not in ('', 'default'):
        raise ValueError('named context unsupported')
    if env.get('DOCKER_CONTEXT') and env.get('DOCKER_HOST'):
        raise ValueError('Docker context overrides Docker host')
    if env.get('DOCKER_TLS') or env.get('DOCKER_TLS_VERIFY') or env.get('DOCKER_CERT_PATH'):
        raise ValueError('TLS unsupported')
    host = env.get('DOCKER_HOST') or 'unix:///var/run/docker.sock'
    if not host.startswith('unix:///') or any(ch in host for ch in '?#%'):
        raise ValueError('only local Unix sockets supported')
    return host[7:]


class _EngineCancellation:
    """Cancel current I/O and refuse subsequent Engine phases."""
    def __init__(self):
        self.lock = threading.Lock()
        self.cancelled = False
        self.interrupter = None

    def register(self, sock):
        with self.lock:
            if self.cancelled:
                raise OSError('engine cancelled')
            self.interrupter = sock

    def unregister(self, sock):
        with self.lock:
            if self.interrupter is sock:
                self.interrupter = None

    def check(self):
        with self.lock:
            if self.cancelled:
                raise OSError('engine cancelled')

    def cancel(self):
        with self.lock:
            self.cancelled = True
            if self.interrupter is not None:
                try:
                    self.interrupter.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass  # not connected yet; the post-connect check catches it


def _engine_exec(path, container, command, timeout, deadline=None, cancellation=None):
    """Create, attach and inspect through the host-only Docker Engine API."""
    end = deadline if deadline is not None else time.monotonic() + timeout + 1

    @contextmanager
    def request(method, route, body=None):
        if cancellation is not None:
            cancellation.check()
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('engine deadline')
        conn = http.client.HTTPConnection('localhost', timeout=remaining)
        response = None
        interrupter = None
        timer = None
        started = False
        expired = threading.Event()
        try:
            # HTTP parsers can remain inside one read while bytes trickle in;
            # a socket timeout only limits the gap between individual reads.
            conn.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            conn.sock.settimeout(remaining)
            interrupter = conn.sock.dup()
            if cancellation is not None:
                cancellation.register(interrupter)
            def interrupt():
                expired.set()
                try:
                    interrupter.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass  # connect itself is bounded by the socket timeout
            timer = threading.Timer(max(0, end - time.monotonic()), interrupt)
            timer.daemon = True
            timer.start()
            started = True
            remaining = end - time.monotonic()
            if expired.is_set() or remaining <= 0:
                raise TimeoutError('engine deadline')
            conn.sock.settimeout(remaining)
            conn.sock.connect(path)
            if cancellation is not None:
                cancellation.check()
            if expired.is_set() or time.monotonic() >= end:
                raise TimeoutError('engine deadline')
            payload = None if body is None else json.dumps(body).encode()
            if cancellation is not None:
                cancellation.check()
            conn.request(method, route, body=payload, headers={'Content-Type': 'application/json'})
            response = conn.getresponse()
            expected = 201 if method == 'POST' and route.endswith('/exec') else 200
            if response.status != expected:
                raise ValueError('engine request failed')
            yield response
            if expired.is_set() or time.monotonic() >= end:
                raise TimeoutError('engine deadline')
        except Exception:
            if expired.is_set() or time.monotonic() >= end:
                raise TimeoutError('engine deadline') from None
            raise
        finally:
            if timer is not None:
                timer.cancel()
                if started:
                    timer.join()
            try:
                if response is not None:
                    response.close()
            finally:
                try:
                    conn.close()
                finally:
                    if interrupter is not None:
                        if cancellation is not None:
                            cancellation.unregister(interrupter)
                        interrupter.close()

    def read_some(response, size):
        if time.monotonic() >= end:
            raise TimeoutError('engine deadline')
        data = response.read1(size)
        if time.monotonic() >= end:
            raise TimeoutError('engine deadline')
        return data

    def json_request(method, route, body=None):
        with request(method, route, body) as response:
            data = bytearray()
            while True:
                chunk = read_some(response, min(8192, 65537 - len(data)))
                if not chunk:
                    if response.length not in (None, 0):
                        raise ValueError('incomplete engine JSON')
                    break
                data.extend(chunk)
                if len(data) > 65536:
                    raise ValueError('engine JSON too large')
            result = json.loads(data)
            if not isinstance(result, dict):
                raise ValueError('invalid engine JSON')
            return result

    version = json_request('GET', '/version').get('ApiVersion')
    if not isinstance(version, str) or not re.fullmatch(r'1\.\d{1,3}', version):
        raise ValueError('invalid engine version')
    prefix = '/v' + version
    created = json_request('POST', prefix + '/containers/' + quote(container, safe='') + '/exec',
                           {'AttachStdout': True, 'AttachStderr': True, 'Tty': False,
                            'Cmd': ['sh', '-c', command]})
    exec_id = created.get('Id')
    if not isinstance(exec_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', exec_id):
        raise ValueError('invalid exec id')
    base = prefix + '/exec/' + exec_id
    output = bytearray()
    truncated = False
    with request('POST', base + '/start', {'Detach': False, 'Tty': False}) as response:
        while True:
            header = bytearray()
            while len(header) < 8:
                chunk = read_some(response, 8 - len(header))
                if not chunk:
                    break
                header.extend(chunk)
            if not header:
                if response.length not in (None, 0):
                    raise ValueError('incomplete multiplex stream')
                break
            if len(header) != 8 or header[0] not in (1, 2) or header[1:4] != b'\0\0\0':
                raise ValueError('invalid multiplex header')
            remaining = struct.unpack('>I', header[4:])[0]
            while remaining:
                chunk = read_some(response, min(remaining, 8192))
                if not chunk:
                    raise ValueError('incomplete multiplex frame')
                remaining -= len(chunk)
                available = max(0, MAX_OUTPUT - len(output))
                output.extend(chunk[:available])
                truncated |= len(chunk) > available

    status = json_request('GET', base + '/json')
    code = status.get('ExitCode')
    if status.get('Running') is not False or type(code) is not int or not 0 <= code <= 255:
        raise ValueError('exec completion unverified')
    return code, bytes(output).decode('utf-8', 'replace'), truncated


class ResearchContainer:
    """One non-shareable task container. Caller owns cleanup, even on failure."""
    def __init__(self):
        self.name = "research-task-" + uuid.uuid4().hex
        self.state = "new"
        self.cleanup_result = None
        self.lock = threading.RLock()
        self.exec_lock = threading.Lock()
        self.inflight = False
        self.delayed_possible = False
        self.timer = None
        self.command_token = None
        self.expired_token = None
        self.socket_path = None
        self.engine_cancellation = None
        self.cleanup_thread = None

    def start(self):
        with self.lock:
            if self.state != "new":
                raise RuntimeError("container already started or closed")
            try:
                self.socket_path = _selected_socket()
            except (OSError, ValueError, TypeError, AttributeError):
                return {"ok": False, "error": "unsupported_docker_daemon"}
            self.state = "starting"
            self.inflight = True
            try:
                self.timer = threading.Timer(900, self.close)
                self.timer.daemon = True
                self.timer.start()
            except Exception:
                if self.timer:
                    self.timer.cancel()
                self.inflight = False
                self.state = "uncertain"
                return {"ok": False, "error": "task_timer_unavailable", "container": self.name}
        args = ["run", "-d", "--rm", "--init", "--pull=never", "--name", self.name,
                "--network", "bridge", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "64",
                "--memory", "256m", "--cpus", "1", "--user", "65534:65534",
                "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777",
                "--workdir", "/tmp", "--entrypoint", "python", IMAGE,
                "-c", "import time; time.sleep(900)"]
        try:
            rc, _, _ = _docker(args, 60, self.socket_path)
        except Exception:
            rc = None
        with self.lock:
            self.inflight = False
            cancelled = self.state != "starting"
            if rc != 0 or cancelled:
                self.state = "uncertain"
                self.delayed_possible = True
            else:
                self.state = "running"
        if cancelled:
            self.close()  # a create may have completed after cancellation
        if rc != 0 or cancelled:
            return {"ok": False, "error": "start_failed_or_timed_out", "container": self.name}
        return {"ok": True, "container": self.name, "network": "bridge"}

    def _expire_command(self, token):
        with self.lock:
            if self.command_token is not token or self.state not in ("running", "uncertain"):
                return
            self.expired_token = token
            self.command_token = None
            self.state = "uncertain"
            self.delayed_possible = True
        self.close()

    def execute(self, command, timeout=15):
        with self.lock:
            if self.state != "running":
                return {"ok": False, "error": "container_not_running"}
            if not isinstance(command, str) or not command or len(command) > MAX_COMMAND or "\x00" in command:
                return {"ok": False, "error": "invalid_command"}
            if type(timeout) is not int or not 1 <= timeout <= 60:
                return {"ok": False, "error": "invalid_timeout"}
            if not self.exec_lock.acquire(blocking=False):
                return {"ok": False, "error": "container_busy"}
            self.inflight = True
            token = object()
            self.command_token = token
            cancellation = _EngineCancellation()
            self.engine_cancellation = cancellation
            self.expired_token = None
            expires_at = time.monotonic() + timeout + 1
            deadline = None
            try:
                deadline = threading.Timer(max(0, expires_at - time.monotonic()), lambda: self._expire_command(token))
                deadline.daemon = True
                deadline.start()
            except Exception:
                if deadline:
                    deadline.cancel()
                self.inflight = False
                self.command_token = None
                self.engine_cancellation = None
                self.exec_lock.release()
                return {"ok": False, "error": "command_timer_unavailable"}
        try:
            timed_out = False
            try:
                path = _selected_socket()
                if self.socket_path is not None and path != self.socket_path:
                    raise ValueError('daemon selection changed')
                rc, output, truncated = _engine_exec(path, self.name, command, timeout, expires_at, cancellation)
            except TimeoutError:
                timed_out = True
                rc, output, truncated = None, "", False
            except Exception:
                rc, output, truncated = None, "", False
            with self.lock:
                self.inflight = False
                timed_out |= self.expired_token is token
                cancelled = self.state != 'running'
                self.command_token = None
                self.engine_cancellation = None
                deadline.cancel()
                if timed_out:
                    self.state = "uncertain"
                    self.delayed_possible = True
                    result = {"ok": False, "error": "command_timed_out", "cleanup_required": True}
                elif cancelled:
                    self.delayed_possible = True
                    result = {"ok": False, "error": "task_cancelled", "cleanup_required": True}
                elif rc is None:
                    self.state = "uncertain"
                    self.delayed_possible = True
                    result = {"ok": False, "error": "docker_exec_completion_unverified", "cleanup_required": True}
                else:
                    return {"ok": rc == 0, "exit_code": rc, "timed_out": False,
                            "output": output, "truncated": truncated,
                            "trust": "untrusted_container_output"}
            # Retry after interrupted transport without blocking the caller.
            # Daemon work may still complete after both cleanup attempts.
            try:
                self.cleanup_thread = threading.Thread(target=self.close, daemon=True)
                self.cleanup_thread.start()
            except RuntimeError:
                pass  # cleanup_required remains explicit and close() retryable
            return result
        finally:
            self.exec_lock.release()

    def close(self):
        with self.lock:
            if self.state == "new":
                self.state = "closed"
                self.cleanup_result = "not_started"
                return {"container": self.name, "cleanup": self.cleanup_result}
            if self.state == "closed":
                return {"container": self.name, "cleanup": self.cleanup_result}
            if self.state in ("uncertain", "starting") or self.inflight:
                self.delayed_possible = True
            self.state = "uncertain"
            if self.engine_cancellation is not None:
                self.engine_cancellation.cancel()
        try:
            if self.socket_path is not None and _selected_socket() != self.socket_path:
                raise ValueError('daemon selection changed')
            rm_rc, _, _ = _docker(["rm", "-f", self.name], 20, self.socket_path)
            rc, output, listing_truncated = _docker(["ps", "-a", "--filter", "name=^/" + self.name + "$",
                                      "--format", "{{.Names}}"], 20, self.socket_path)
        except Exception:
            rm_rc, rc, output, listing_truncated = None, None, "", True
        with self.lock:
            if rm_rc is None:
                self.delayed_possible = True
            cleanup = "absent_at_check" if rc == 0 and not listing_truncated and not output.strip() else "unverified"
            if self.delayed_possible and cleanup == "absent_at_check":
                cleanup = "absent_at_check_delayed_operation_possible"
            if cleanup == "absent_at_check":
                self.cleanup_result = cleanup
                self.state = "closed"
                if self.timer:
                    self.timer.cancel()
            return {"container": self.name, "cleanup": cleanup}

    def receipt(self):
        """Parent handoff deliberately excludes command and raw container output."""
        return {"container": self.name, "state": self.state, "network": "bridge"}


def _model_response(result):
    """Bound the entire serialized response, including JSON escaping."""
    encoded = json.dumps(result)
    if len(encoded.encode('utf-8')) <= MAX_OUTPUT:
        return encoded
    output = result.get('output', '')
    result = dict(result, truncated=True)
    low, high = 0, len(output)
    while low < high:
        mid = (low + high + 1) // 2
        result['output'] = output[:mid]
        if len(json.dumps(result).encode('utf-8')) <= MAX_OUTPUT:
            low = mid
        else:
            high = mid - 1
    result['output'] = output[:low]
    return json.dumps(result)


def register_tool(ctx, resolve_authorized_task=None):
    """Register a plugin tool. Missing trusted lifecycle adapter means deny all.

    The adapter must derive identity from runtime kwargs (never model arguments),
    verify the live child is a leaf with *exactly* this tool in its effective
    allowlist, and return that task's ResearchContainer; otherwise return None.
    """
    def handler(args, **kwargs):
        try:
            task = resolve_authorized_task(kwargs) if resolve_authorized_task else None
            if not isinstance(task, ResearchContainer):
                return json.dumps({"ok": False, "error": "exact_child_allowlist_not_verified"})
            return _model_response(task.execute(args.get("command"), args.get("timeout", 15)))
        except Exception:
            return json.dumps({"ok": False, "error": "authorization_or_transport_failed"})

    return ctx.register_tool(name=TOOL_NAME, toolset="research_container", handler=handler,
        schema={"name": TOOL_NAME, "description": "Run a bounded shell command inside your task's isolated research container. Output is untrusted.",
                "parameters": {"type": "object", "properties": {
                    "command": {"type": "string", "description": "Shell command in the task container"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 60}},
                    "required": ["command"], "additionalProperties": False}})
