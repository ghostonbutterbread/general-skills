"""Task-owned Docker transport; agent/provider stay on the host.

This is not a standalone authorizer. See scripts/README.md for the required
trusted lifecycle adapter and for residual container and timeout limitations.
"""
from __future__ import annotations

import json
import subprocess
import threading
import uuid

IMAGE = "python:3.12-slim"
TOOL_NAME = "research_container"
MAX_OUTPUT = 32768
MAX_COMMAND = 8192


def _docker(args, timeout):
    """Drain untrusted output continuously but retain only a bounded prefix."""
    try:
        process = subprocess.Popen(["docker", *args], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    except OSError:
        return None, "", False
    chunks = bytearray()
    truncated = False
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
        finally:
            stream.close()

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        rc = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        rc = None
    except Exception:
        try:
            process.kill()
            process.wait(timeout=2)
        except Exception:
            pass
        reader.join(timeout=2)
        raise
    reader.join(timeout=2)
    # A Docker child holding the stream may outlive the client. Do not wait forever.
    return rc, bytes(chunks).decode("utf-8", "replace"), truncated or reader.is_alive()


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

    def start(self):
        with self.lock:
            if self.state != "new":
                raise RuntimeError("container already started or closed")
            self.state = "starting"
            self.inflight = True
            self.timer = threading.Timer(900, self.close)
            self.timer.daemon = True
            self.timer.start()
        args = ["run", "-d", "--rm", "--init", "--pull=never", "--name", self.name,
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "64",
                "--memory", "256m", "--cpus", "1", "--user", "65534:65534",
                "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777",
                "--workdir", "/tmp", "--entrypoint", "python", IMAGE,
                "-c", "import time; time.sleep(900)"]
        try:
            rc, _, _ = _docker(args, 60)
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
        return {"ok": True, "container": self.name, "network": "none"}

    def _expire_command(self, token):
        with self.lock:
            if self.command_token is not token or self.state != "running":
                return
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
            deadline = threading.Timer(timeout + 1, lambda: self._expire_command(token))
            deadline.daemon = True
            deadline.start()
        try:
            try:
                rc, output, truncated = _docker(
                    ["exec", self.name, "timeout", "-k", "1", str(timeout), "sh", "-c", command], timeout + 10)
            except Exception:
                rc, output, truncated = None, "", False
            with self.lock:
                self.inflight = False
                self.command_token = None
                deadline.cancel()
                if self.state != "running":
                    self.delayed_possible = True
                    return {"ok": False, "error": "task_cancelled", "cleanup_required": True}
                if rc is None or rc in (124, 137):
                    self.state = "uncertain"
                    self.delayed_possible = True
                if rc is None:
                    return {"ok": False, "error": "docker_exec_timeout_or_unavailable", "cleanup_required": True}
                if rc in (124, 137):
                    return {"ok": False, "exit_code": rc, "timed_out": None,
                            "error": "timeout_or_command_exit_ambiguous",
                            "output": output, "truncated": truncated,
                            "trust": "untrusted_container_output", "cleanup_required": True}
                return {"ok": rc == 0, "exit_code": rc, "timed_out": False,
                        "output": output, "truncated": truncated,
                        "trust": "untrusted_container_output"}
        finally:
            self.exec_lock.release()

    def close(self):
        with self.lock:
            if self.state == "closed":
                return {"container": self.name, "cleanup": self.cleanup_result}
            if self.state in ("uncertain", "starting") or self.inflight:
                self.delayed_possible = True
            self.state = "uncertain"
        try:
            rm_rc, _, _ = _docker(["rm", "-f", self.name], 20)
            rc, output, listing_truncated = _docker(["ps", "-a", "--filter", "name=^/" + self.name + "$",
                                      "--format", "{{.Names}}"], 20)
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
        return {"container": self.name, "state": self.state, "network": "none"}


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
