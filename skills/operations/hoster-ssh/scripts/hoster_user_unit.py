#!/usr/bin/env python3
"""Dispatch a remote foreground command into a bounded Hoster user-systemd service."""

from __future__ import annotations

import argparse
import base64
import json
import re
import shlex
import subprocess
import sys
from typing import Sequence

UNIT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")

REMOTE_RUNNER = r'''
import base64
import json
import os
import subprocess
import sys

payload = json.loads(base64.b64decode(os.environ["HOSTER_UNIT_PAYLOAD"]))
os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={os.environ['XDG_RUNTIME_DIR']}/bus"

manager = subprocess.run(
    ["systemctl", "--user", "is-system-running"], text=True, capture_output=True, check=False
)
if manager.stdout.strip() not in {"running", "degraded"}:
    print(
        "Hoster user systemd manager is unavailable: " + (manager.stdout or manager.stderr).strip(),
        file=sys.stderr,
    )
    raise SystemExit(1)

command = [
    "systemd-run",
    "--user",
    f"--unit={payload['unit']}",
    f"--property=MemoryHigh={payload['memory_high']}",
    f"--property=MemoryMax={payload['memory_max']}",
    f"--property=CPUWeight={payload['cpu_weight']}",
    "--",
    *payload["command"],
]
started = subprocess.run(command, check=False)
if started.returncode:
    raise SystemExit(started.returncode)

status = subprocess.run(
    [
        "systemctl",
        "--user",
        "show",
        payload["unit"],
        "-p",
        "ActiveState",
        "-p",
        "ControlGroup",
        "-p",
        "MemoryHigh",
        "-p",
        "MemoryMax",
    ],
    text=True,
    check=False,
)
print(status.stdout, end="")
raise SystemExit(status.returncode)
'''.strip()


def validate_unit_name(unit: str) -> str:
    if not UNIT_NAME.fullmatch(unit):
        raise ValueError("unit must contain only letters, numbers, '.', '_', '@', or '-' and start with a letter or number")
    return unit


def build_run_invocation(
    *,
    host: str,
    identity_file: str,
    unit: str,
    memory_high: str,
    memory_max: str,
    cpu_weight: int,
    command: Sequence[str],
) -> list[str]:
    """Return a safe one-shot SSH invocation for a bounded user-systemd service."""
    validate_unit_name(unit)
    if not command:
        raise ValueError("command is required")
    if cpu_weight < 1 or cpu_weight > 10000:
        raise ValueError("cpu_weight must be between 1 and 10000")

    payload = base64.b64encode(
        json.dumps(
            {
                "unit": unit,
                "memory_high": memory_high,
                "memory_max": memory_max,
                "cpu_weight": cpu_weight,
                "command": list(command),
            },
            separators=(",", ":"),
        ).encode()
    ).decode()
    remote_command = (
        f"HOSTER_UNIT_PAYLOAD={shlex.quote(payload)} "
        f"exec python3 -c {shlex.quote(REMOTE_RUNNER)}"
    )
    return [
        "ssh",
        "-i",
        identity_file,
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ControlMaster=no",
        "-T",
        host,
        remote_command,
    ]


def run(args: argparse.Namespace) -> int:
    invocation = build_run_invocation(
        host=args.host,
        identity_file=args.identity_file,
        unit=args.unit,
        memory_high=args.memory_high,
        memory_max=args.memory_max,
        cpu_weight=args.cpu_weight,
        command=args.command,
    )
    return subprocess.run(invocation, check=False).returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="ryushe@hoster", help="SSH destination (default: ryushe@hoster)")
    parser.add_argument("--identity-file", default="/home/ryushe/.ssh/hoster", help="SSH private-key path")
    parser.add_argument("--unit", required=True, help="Unique user-systemd service name")
    parser.add_argument("--memory-high", default="2G", help="systemd MemoryHigh value")
    parser.add_argument("--memory-max", default="3G", help="systemd MemoryMax value")
    parser.add_argument("--cpu-weight", type=int, default=100, help="systemd CPUWeight (1-10000)")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after '--'")
    args = parser.parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after '--'")
    try:
        return run(args)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
