---
name: hoster-ssh
description: Use when dispatching, supervising, attaching to, or diagnosing work on Hoster over SSH. Keeps durable workloads out of ssh.service through bounded user-systemd services.
---

# Hoster SSH

## Overview

SSH is Hoster's **control plane**, never its process supervisor. A browser,
agent CLI, proxy, `tmux` session, or background command started directly from
an SSH login inherits `ssh.service`; detaching with `nohup`, `setsid`, or bare
`tmux` does not change that cgroup. Such descendants can make new SSH
handshakes stall during resource pressure or an unclean service restart.

Use this skill whenever the target is `hoster` / `10.0.0.10`, including a
browser or agent launched indirectly by another skill. It owns remote workload
lifecycle. Use normal one-shot SSH only for bounded inspection and dispatch.

## Connection

- Host: `hoster` (`10.0.0.10`)
- User: `ryushe`
- Key: General Skills config `hoster.identity_file` (default: `~/.ssh/hoster`). Override it persistently in the generated config, for one run with `HOSTER_SSH_KEY`, or explicitly with `--identity-file`.
- Required Hoster prerequisite: `loginctl show-user ryushe -p Linger` reports
  `Linger=yes`.

Bounded inspection:

```bash
ssh -i "${HOSTER_SSH_KEY:-$HOME/.ssh/hoster}" \
  -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T \
  ryushe@hoster 'hostname; uptime'
```

## Durable Launch Contract

1. **Check for a reusable healthy run first.** Inspect the task's recorded
   systemd unit, CDP port, tmux session, or run manifest before launching a
   replacement. Attach to a healthy matching run; clean up only a prior run
   proven to belong to this task. Completion: the selected run identity and
   owner are recorded.
2. **Dispatch durable work with the helper below.** It creates a named bounded
   `systemd --user` **service** beneath the user manager, rather than beneath
   `ssh.service`. The dispatched command must remain foreground for the workload
   lifetime (or run a task-owned supervisor that does); this lets systemd retain
   its cgroup, budgets, and cleanup authority.
3. **Close SSH after dispatch.** Do not leave an interactive shell or transport
   open just to keep work running. Completion: no task-owned `ssh ... hoster`
   client remains, except a deliberately recorded temporary tunnel.
4. **Verify ownership before proceeding.** The unit ControlGroup must be below
   `/user.slice/...`, never `/system.slice/ssh.service`.
5. **Stop the unit—not SSH—when the task ends.** Remove task-owned profiles,
   ports, tunnels, and manifests after confirming they belong to that run.

## Dispatch Helper

The canonical helper is colocated with this skill:

```bash
HELPER="$HOME/.hermes/synced-skills/hoster-ssh/scripts/hoster_user_unit.py"
# The helper generates $XDG_CONFIG_HOME/general-skills/config.toml (or
# ~/.config/general-skills/config.toml) on first use. Edit [hoster]
# identity_file there for a persistent override; HOSTER_SSH_KEY wins per run.

run_id="$(date -u +%Y%m%dT%H%M%SZ)"
python3 "$HELPER" \
  --unit="hoster-agent-$run_id" \
  --memory-high=2G --memory-max=3G --cpu-weight=100 \
  -- /bin/bash -lc 'cd <remote-project-dir> && exec <agent-command>'
```

The helper uses one-shot SSH and runs this shape remotely:

```text
systemd-run --user --unit=<run-id>
  MemoryHigh=<budget> MemoryMax=<budget> CPUWeight=<weight> -- <foreground-command>
```

It sets `XDG_RUNTIME_DIR` and `DBUS_SESSION_BUS_ADDRESS`, verifies the user
manager is running, validates unit names, and preserves command argv. Do not
replace it with bare `tmux`, `nohup`, `setsid`, or `&` from SSH. For incident
diagnosis and resource-change safety, see
[`references/systemd-cgroup-isolation.md`](references/systemd-cgroup-isolation.md).

For an interactive CLI that Ryushe must attach to, start the named tmux session
**inside** the dispatched service and keep that service foreground with its
owned supervisor:

```bash
python3 "$HELPER" --unit="hoster-claude-$run_id" -- \
  /bin/bash -lc 'tmux new-session -d -s hoster-claude-'"$run_id"' "exec claude"; exec sleep infinity'
```

## Workspace Attach and Recovery

For the persistent `hoster-ghost-workspace.service`, use the remote `hoster-workspace` wrapper rather than a direct service restart. A normal attach starts an inactive service, waits briefly for its named tmux socket, snapshots non-secret topology, and attaches. It never restarts an active service.

```bash
ssh hoster-workspace
```

Before adding an interactive Claude or Codex pane, record non-secret resume metadata: label, agent kind, session ID, cwd, and intended tmux position. Do not record credentials, bearer URLs, terminal scrollback, or prompts.

```bash
STATE="$HOME/.local/lib/hoster-workspace/hoster_workspace_state.py"
python3 "$STATE" --record --label research-1 --agent claude --resume-id <session-id> \
  --cwd /absolute/project/path --session workspace --window claude-pair-1 --pane 0
python3 "$STATE" --snapshot
```

Snapshots write `~/.local/state/hoster-workspace/latest.json` and a dated copy. If a socket/session is absent while the service is active, normal attach fails closed. Inspect first; run `hoster-workspace --repair-empty` only after proving no workspace session exists. Never make this repair automatic: restarting the service kills all workspace panes.

## Inspect, Attach, and Stop

Use the same user-systemd environment for all remote lifecycle operations:

```bash
ssh -i "${HOSTER_SSH_KEY:-$HOME/.ssh/hoster}" -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T \
  ryushe@hoster '
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
    systemctl --user show hoster-agent-<run-id> \
      -p ActiveState -p ControlGroup -p MemoryCurrent -p MemoryHigh -p MemoryMax
  '
```

Attach only after proving the tmux session belongs to the named unit:

```bash
# Run from a Hoster console or through a temporary, recorded SSH session.
tmux attach -t hoster-claude-<run-id>
```

Stop only the task-owned unit:

```bash
ssh -i "${HOSTER_SSH_KEY:-$HOME/.ssh/hoster}" -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T \
  ryushe@hoster '
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
    systemctl --user stop hoster-agent-<run-id>
    systemctl --user reset-failed hoster-agent-<run-id>
  '
```

Never restart `ssh.service` as ordinary cleanup. It can disrupt access and
will not safely classify which descendants belong to which task.

## Common Pitfalls

1. **`Linger=yes` alone is not isolation.** It enables the user manager; only
   a `systemd-run --user` launch moves work under it.
2. **`start_new_session=True`, `setsid`, `nohup`, and detached tmux are not
   cgroup migration.** They may survive shell exit but still belong to
   `ssh.service`.
3. **Do not attach to a process merely because it is old.** Match the run ID,
   artifact/profile path, unit, and task intent first.
4. **Do not increase `MaxStartups` without evidence.** A TCP/22 connection
   that never receives a banner is commonly host/service starvation, not an
   admission-limit problem.
5. **Do not leave permanent SSH tunnels.** Record a temporary tunnel's local
   PID and close it as soon as the CDP/interactive step completes.

## Verification Checklist

- [ ] `loginctl show-user ryushe -p Linger` says `Linger=yes` on Hoster.
- [ ] Each durable launch has a unique `hoster-<kind>-<run-id>` unit name.
- [ ] `systemctl --user show` reports a ControlGroup below the user manager,
      not `ssh.service`.
- [ ] Every run has a known owner, status/attach path, and stop command.
- [ ] Task-owned SSH clients are closed after dispatch; any temporary tunnel is
      recorded and removed.
- [ ] No bare remote `tmux`, `nohup`, `setsid`, or background launch remains in
      a Hoster-targeting skill or wrapper.
