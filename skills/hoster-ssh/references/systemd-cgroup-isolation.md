# Hoster systemd cgroup isolation

## Incident pattern

Processes started by an SSH login inherit `ssh.service`'s cgroup. A detached
`tmux`, browser, agent, proxy, or child therefore does **not** escape SSH just
because its shell session ends. Under pressure, TCP/22 may accept connections
while the SSH banner or authentication stalls.

Do not tune `MaxStartups` or exempt an IP unless logs prove admission limits are
the cause. First distinguish admission failures from host/cgroup starvation.

## Required model

1. Confirm `loginctl show-user ryushe -p Linger` returns `Linger=yes`.
2. Export `XDG_RUNTIME_DIR=/run/user/$(id -u)` and
   `DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus` for remote control
   commands.
3. Confirm the user manager is `running` or `degraded`.
4. Dispatch durable work with the canonical `hoster-ssh` helper into a unique,
   bounded `systemd-run --user` service.
5. Verify its `ControlGroup` is below
   `/user.slice/.../user@UID.service/app.slice/`, never `/system.slice/ssh.service`.
6. Stop the named user service—not `ssh.service`—to clean up its descendants.

## Before a resource restart

Inventory user units, tmux sessions, browsers, agents, proxies, and tunnels;
state which workloads will be interrupted; record observed CPU, RAM, swap, and
pressure evidence; and use graceful shutdown/reboot. Afterwards, re-check
resource totals, pressure, and the user-systemd bus before accepting new work.
