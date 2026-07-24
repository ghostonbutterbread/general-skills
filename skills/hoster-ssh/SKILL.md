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
- Key: `/home/ryushe/.ssh/hoster`
- Required Hoster prerequisite: `loginctl show-user ryushe -p Linger` reports
  `Linger=yes`.

Bounded inspection:

```bash
ssh -i /home/ryushe/.ssh/hoster \
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
HELPER=/home/ryushe/.openclaw/workspace/skills/hoster-ssh/scripts/hoster_user_unit.py
# In Hermes-only environments use ~/.hermes/synced-skills/hoster-ssh/scripts/hoster_user_unit.py.

run_id="$(date -u +%Y%m%dT%H%M%SZ)"
python3 "$HELPER" \
  --unit="hoster-agent-$run_id" \
  --memory-high=2G --memory-max=3G --cpu-weight=100 \
  -- /bin/bash -lc 'cd /home/ryushe/projects/bug_bounty_harness-stable && exec <agent-command>'
```

The helper uses one-shot SSH and runs this shape remotely:

```text
systemd-run --user --unit=<run-id>
  MemoryHigh=<budget> MemoryMax=<budget> CPUWeight=<weight> -- <foreground-command>
```

It sets `XDG_RUNTIME_DIR` and `DBUS_SESSION_BUS_ADDRESS`, verifies the user
manager is running, validates unit names, and preserves command argv. Do not
replace it with bare `tmux`, `nohup`, `setsid`, or `&` from SSH.

For an interactive CLI that Ryushe must attach to, start the named tmux session
**inside** the dispatched service and keep that service foreground with its
owned supervisor:

```bash
python3 "$HELPER" --unit="hoster-claude-$run_id" -- \
  /bin/bash -lc 'tmux new-session -d -s hoster-claude-'"$run_id"' "exec claude"; exec sleep infinity'
```

## Inspect, Attach, and Stop

Use the same user-systemd environment for all remote lifecycle operations:

```bash
ssh -i /home/ryushe/.ssh/hoster -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T \
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
ssh -i /home/ryushe/.ssh/hoster -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T \
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
