#!/usr/bin/env python3
"""Fail-closed runtime probe for a future disposable research agent, not an agent."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import uuid

# Fixed image and executable: no attacker-supplied Docker options or commands.
IMAGE = "python:3.12-slim"
PROBE = r'''
import json, os, pathlib, socket
name, host_path = os.environ["PROBE_NAME"], os.environ["PROBE_PATH"]
checks = {
    "nonroot": os.getuid() == 65534,
    "canary_env_absent": name not in os.environ,
    "host_canary_absent": not pathlib.Path(host_path).exists(),
    "network_none": set(os.listdir("/sys/class/net")) == {"lo"},
    "root_read_only": "ro" in next(line.split()[5].split(",") for line in pathlib.Path("/proc/self/mountinfo").read_text().splitlines() if line.split()[4] == "/"),
}
print(json.dumps(checks, sort_keys=True))
'''
EXPECTED = {"nonroot", "canary_env_absent", "host_canary_absent", "network_none", "root_read_only"}


def docker(args: list[str], timeout: int, env: dict[str, str] | None = None) -> tuple[int | None, str, str]:
    # Files instead of pipes prevent a surviving Docker child holding a pipe open
    # from defeating subprocess timeout cleanup. Scratch inherits restrictive umask.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            p = subprocess.Popen(["docker", *args], stdout=out, stderr=err, env=env)
        except OSError as exc:
            return None, "", str(exc)
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            rc = None
        out.seek(0)
        err.seek(0)
        return rc, out.read(8192).decode("utf-8", "replace"), err.read(8192).decode("utf-8", "replace")


def probe(timeout: int) -> dict:
    container = "research-worker-preflight-" + uuid.uuid4().hex
    canary_name = "RESEARCH_HOST_CANARY_" + secrets.token_hex(12).upper()
    canary_value = secrets.token_hex(32)
    result = {"kind": "research-worker-preflight", "agent_executed": False,
              "probe_passed": False, "container": container, "image": IMAGE,
              "checks": {}, "cleanup": "not_attempted"}
    # The canary is task-owned and outside all container mounts.
    with tempfile.TemporaryDirectory(prefix="research-worker-canary-") as directory:
        path = Path(directory) / "host-only"
        path.write_text(canary_value, encoding="utf-8")
        env = os.environ.copy()
        env[canary_name] = canary_value
        args = ["run", "--rm", "--pull=never", "--name", container,
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "64",
                "--memory", "128m", "--cpus", "1", "--user", "65534:65534",
                "--env", "PROBE_NAME=" + canary_name,
                "--env", "PROBE_PATH=" + str(path),
                "--entrypoint", "python", IMAGE, "-c", PROBE]
        try:
            rc, out, err = docker(args, timeout, env)
            if rc is None:
                result["error"] = "container probe timed out or Docker could not be started"
            elif rc != 0:
                result["error"] = "container probe failed (exit %d)" % rc
            else:
                try:
                    checks = json.loads(out)
                    if not isinstance(checks, dict) or set(checks) != EXPECTED or any(type(v) is not bool for v in checks.values()):
                        raise ValueError("invalid check response")
                    result["checks"] = checks
                    if not all(checks.values()):
                        result["error"] = "one or more isolation checks failed"
                except (ValueError, json.JSONDecodeError):
                    result["error"] = "invalid container probe response"
        finally:
            # Exact generated name only; never prune unrelated containers.
            docker(["rm", "-f", container], min(timeout, 5))
            code, out, _ = docker(["ps", "-a", "--filter", "name=^/" + container + "$", "--format", "{{.Names}}"], min(timeout, 5))
            result["cleanup"] = "absent_at_check" if code == 0 and not out.strip() else "unverified"
    result["probe_passed"] = bool(result["checks"]) and all(result["checks"].values()) and result["cleanup"] == "absent_at_check"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=20, help="Docker operation timeout in seconds (1-120)")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 120:
        parser.error("timeout must be between 1 and 120 seconds")
    result = probe(args.timeout)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["probe_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
