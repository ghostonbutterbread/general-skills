#!/usr/bin/env python3
"""Inspect and optionally reap completed, explicitly registered tmux child scopes.

A scope is eligible only when it was registered while its live tmux pane and
server identity were verified, that identity still matches systemd metadata, and
the scope is completely empty. A remaining process, including `ssh-agent`, is
reported but never stopped because arbitrary tmux sockets cannot be safely
enumerated. Ordinary tmux panes and unregistered scopes are never cleanup
candidates.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import TypedDict

DESCRIPTION = re.compile(r"^tmux child pane (\d+) launched by process (\d+)$")


class ProcessRow(TypedDict):
    pid: int
    command: str


class ScopeRecord(TypedDict):
    scope: str
    control_group: str
    original_pane_pid: int
    launcher_pid: int
    socket_path: str


def run(*argv: str) -> str:
    return subprocess.run(argv, check=True, text=True, capture_output=True).stdout


def registry_path() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return Path(os.environ.get("HOSTER_TMUX_SPAWN_REGISTRY", state_home / "hoster-workspace/tmux-spawn-scopes.json"))


def load_registry(path: Path) -> dict[str, ScopeRecord]:
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    if not isinstance(raw, dict) or not isinstance(raw.get("scopes"), list):
        raise ValueError(f"invalid registry: {path}")
    records: dict[str, ScopeRecord] = {}
    for row in raw["scopes"]:
        if not isinstance(row, dict):
            continue
        try:
            record: ScopeRecord = {
                "scope": str(row["scope"]),
                "control_group": str(row["control_group"]),
                "original_pane_pid": int(row["original_pane_pid"]),
                "launcher_pid": int(row["launcher_pid"]),
                "socket_path": str(row["socket_path"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        records[record["scope"]] = record
    return records


def save_registry(path: Path, records: dict[str, ScopeRecord]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {"version": 1, "scopes": [records[name] for name in sorted(records)]}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def tmux_sockets() -> list[Path]:
    directory = Path("/tmp") / f"tmux-{os.getuid()}"
    return sorted(path for path in directory.glob("*") if path.is_socket())


def pane_inventory() -> tuple[set[int], dict[int, set[str]]]:
    pane_pids: set[int] = set()
    server_sockets: dict[int, set[str]] = {}
    for socket in tmux_sockets():
        socket_text = str(socket)
        try:
            server_pid = int(run("tmux", "-S", socket_text, "display-message", "-p", "#{pid}").strip())
            rows = run("tmux", "-S", socket_text, "list-panes", "-a", "-F", "#{pane_pid}")
        except (subprocess.CalledProcessError, ValueError):
            continue
        server_sockets.setdefault(server_pid, set()).add(socket_text)
        pane_pids.update(int(value) for value in rows.split() if value.isdigit())
    return pane_pids, server_sockets


def scopes() -> list[str]:
    output = run(
        "systemctl", "--user", "list-units", "--type=scope", "--state=running",
        "--no-legend", "--no-pager", "tmux-spawn-*",
    )
    return [line.split(maxsplit=1)[0] for line in output.splitlines() if line.strip()]


def properties(scope: str) -> dict[str, str]:
    output = run(
        "systemctl", "--user", "show", scope,
        "-p", "Description", "-p", "ControlGroup", "-p", "ActiveState",
    )
    return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)


def cgroup_processes(control_group: str) -> list[ProcessRow]:
    path = Path("/sys/fs/cgroup") / control_group.lstrip("/") / "cgroup.procs"
    try:
        pids = [int(value) for value in path.read_text().split()]
    except FileNotFoundError:
        return []
    rows: list[ProcessRow] = []
    for pid in pids:
        try:
            command = Path(f"/proc/{pid}/comm").read_text().strip()
        except FileNotFoundError:
            continue
        rows.append({"pid": pid, "command": command})
    return rows


def metadata(scope: str) -> tuple[dict[str, str], int | None, int | None]:
    props = properties(scope)
    match = DESCRIPTION.fullmatch(props.get("Description", ""))
    if not match:
        return props, None, None
    return props, int(match.group(1)), int(match.group(2))


def register(scope: str, records: dict[str, ScopeRecord]) -> ScopeRecord:
    props, pane_pid, launcher_pid = metadata(scope)
    active_panes, server_sockets = pane_inventory()
    if props.get("ActiveState") != "active" or pane_pid is None or launcher_pid is None:
        raise ValueError("scope does not have an active recognized tmux-child identity")
    if pane_pid not in active_panes:
        raise ValueError("original pane is not live; refusing late registration")
    sockets = server_sockets.get(launcher_pid, set())
    if len(sockets) != 1:
        raise ValueError("launcher is not uniquely identified as a live tmux server")
    record: ScopeRecord = {
        "scope": scope,
        "control_group": props.get("ControlGroup", ""),
        "original_pane_pid": pane_pid,
        "launcher_pid": launcher_pid,
        "socket_path": next(iter(sockets)),
    }
    records[scope] = record
    return record


def register_pane(pane_pid: int, records: dict[str, ScopeRecord]) -> ScopeRecord:
    matches = []
    for scope in scopes():
        _, original_pane_pid, _ = metadata(scope)
        if original_pane_pid == pane_pid:
            matches.append(scope)
    if len(matches) != 1:
        raise ValueError("pane does not resolve to exactly one active tmux child scope")
    return register(matches[0], records)


def candidate(scope: str, records: dict[str, ScopeRecord], active_panes: set[int]) -> dict[str, object]:
    props, original_pid, launcher_pid = metadata(scope)
    processes = cgroup_processes(props.get("ControlGroup", ""))
    process_pids = {row["pid"] for row in processes}
    record = records.get(scope)
    reasons = []
    if props.get("ActiveState") != "active":
        reasons.append("not-active")
    if original_pid is None or launcher_pid is None:
        reasons.append("unrecognized-description")
    if record is None:
        reasons.append("unregistered-scope")
    elif (record["control_group"] != props.get("ControlGroup", "") or record["original_pane_pid"] != original_pid or record["launcher_pid"] != launcher_pid):
        reasons.append("registry-mismatch")
    if original_pid in active_panes:
        reasons.append("original-pane-still-live")
    if process_pids & active_panes:
        reasons.append("current-pane-process-in-scope")
    if processes:
        reasons.append("process-remains")
    return {
        "scope": scope,
        "original_pane_pid": original_pid,
        "processes": processes,
        "registered": record is not None,
        "eligible": not reasons,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    registrations = parser.add_mutually_exclusive_group()
    registrations.add_argument("--register", metavar="SCOPE", help="Record a currently live, verified tmux-child scope.")
    registrations.add_argument("--register-pane", metavar="PID", type=int, help="Record the live tmux-child scope owning pane PID.")
    parser.add_argument("--apply", action="store_true", help="Stop only eligible stale scopes.")
    args = parser.parse_args()
    path = registry_path()
    records = load_registry(path)
    if args.register or args.register_pane is not None:
        record = register(args.register, records) if args.register else register_pane(args.register_pane, records)
        save_registry(path, records)
        print(json.dumps({"registered": record, "registry": str(path)}, sort_keys=True))
        return 0
    active_panes, _ = pane_inventory()
    rows = [candidate(scope, records, active_panes) for scope in scopes()]
    stopped = []
    if args.apply:
        # Re-check the exact scope and its process list immediately before mutation.
        active_panes, _ = pane_inventory()
        for row in rows:
            fresh = candidate(str(row["scope"]), records, active_panes)
            if fresh["eligible"]:
                run("systemctl", "--user", "stop", str(fresh["scope"]))
                stopped.append(str(fresh["scope"]))
    print(json.dumps({
        "apply": args.apply,
        "registry": str(path),
        "active_pane_pids": sorted(active_panes),
        "scopes": rows,
        "stopped": stopped,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
