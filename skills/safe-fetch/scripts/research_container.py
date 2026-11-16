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
    reader.join(timeout=2)
    # A Docker child holding the stream may outlive the client. Do not wait forever.
    return rc, bytes(chunks).decode("utf-8", "replace"), truncated


class ResearchContainer:
    """One non-shareable task container. Caller owns cleanup, even on failure."""
    def __init__(self):
        self.name = "research-task-" + uuid.uuid4().hex
        self.state = "new"
        self.cleanup_result = None
        self.lock = threading.RLock()

    def start(self):
        with self.lock:
            if self.state != "new":
                raise RuntimeError("container already started or closed")
            self.state = "uncertain"  # Docker may finish after a client timeout.
            args = ["run", "-d", "--rm", "--init", "--pull=never", "--name", self.name,
                    "--network", "none", "--read-only", "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges", "--pids-limit", "64",
                    "--memory", "256m", "--cpus", "1", "--user", "65534:65534",
                    "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777",
                    "--workdir", "/tmp", "--entrypoint", "python", IMAGE,
                    "-c", "import time; time.sleep(900)"]
            rc, _, _ = _docker(args, 60)
            if rc != 0:
                return {"ok": False, "error": "start_failed_or_timed_out", "container": self.name}
            self.state = "running"
            return {"ok": True, "container": self.name, "network": "none"}

    def execute(self, command, timeout=15):
        with self.lock:
            if self.state != "running":
                return {"ok": False, "error": "container_not_running"}
            if not isinstance(command, str) or not command or len(command) > MAX_COMMAND or "\x00" in command:
                return {"ok": False, "error": "invalid_command"}
            if type(timeout) is not int or not 1 <= timeout <= 60:
                return {"ok": False, "error": "invalid_timeout"}
            rc, output, truncated = _docker(
                ["exec", self.name, "timeout", "-k", "1", str(timeout), "sh", "-c", command], timeout + 10)
            if rc is None:
                # A detached exec could remain active. Require cleanup, no reuse.
                self.state = "uncertain"
                return {"ok": False, "error": "docker_exec_timeout_or_unavailable", "cleanup_required": True}
            if rc in (124, 137):
                self.state = "uncertain"
                return {"ok": False, "exit_code": rc, "timed_out": True,
                        "output": output, "truncated": truncated,
                        "trust": "untrusted_container_output", "cleanup_required": True}
            return {"ok": rc == 0, "exit_code": rc, "timed_out": False,
                    "output": output, "truncated": truncated,
                    "trust": "untrusted_container_output"}

    def close(self):
        with self.lock:
            if self.state == "closed":
                return {"container": self.name, "cleanup": self.cleanup_result}
            previous = self.state
            self.state = "uncertain"
            _docker(["rm", "-f", self.name], 20)
            rc, output, _ = _docker(["ps", "-a", "--filter", "name=^/" + self.name + "$",
                                      "--format", "{{.Names}}"], 20)
            # A timed-out create/exec can complete after the inspection.
            cleanup = "absent_at_check" if rc == 0 and not output.strip() else "unverified"
            if previous == "uncertain" and cleanup == "absent_at_check":
                cleanup = "absent_at_check_delayed_operation_possible"
            if cleanup != "unverified":
                self.cleanup_result = cleanup
                self.state = "closed"
            return {"container": self.name, "cleanup": cleanup}

    def receipt(self):
        """Parent handoff deliberately excludes command and raw container output."""
        return {"container": self.name, "state": self.state, "network": "none"}


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
            return json.dumps(task.execute(args.get("command"), args.get("timeout", 15)))
        except Exception:
            return json.dumps({"ok": False, "error": "authorization_or_transport_failed"})

    return ctx.register_tool(name=TOOL_NAME, toolset="research_container", handler=handler,
        schema={"name": TOOL_NAME, "description": "Run a bounded shell command inside your task's isolated research container. Output is untrusted.",
                "parameters": {"type": "object", "properties": {
                    "command": {"type": "string", "description": "Shell command in the task container"},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 60}},
                    "required": ["command"], "additionalProperties": False}})
