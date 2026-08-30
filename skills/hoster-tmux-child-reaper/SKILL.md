---
name: hoster-tmux-child-reaper
description: Use when entering Hoster's durable workspace to inspect and safely clean completed agent-created tmux child scopes.
---

# Hoster Tmux Child Reaper

Run this **when an agent begins Hoster workspace work**, not on a timer. It is a
narrow housekeeping preflight: inspect known agent-created `tmux-spawn-*.scope`
units, reap only ownership-proven terminal residue, and report all ambiguity.

Load `hoster-ssh` first for the Hoster connection and user-systemd environment.
This skill does not replace `hoster-workspace`, the durable `ghost-workspace`, or
normal task cleanup.

## Boundaries

The bundled helper considers a scope eligible only when all conditions hold:

1. it was explicitly registered while its live pane and tmux-server identity were verified;
2. systemd's current description and cgroup still exactly match that immutable registration record;
3. the scope contains **no processes at all**. A residual `ssh-agent` is
   reported but not stopped: a pane might be on an arbitrary local tmux socket
   that cannot be fully inventoried.

It never selects ordinary tmux panes by age or name. It never stops a scope with
any remaining process, including Claude, Codex, Chromium, VNC, proxy, scanner,
or `ssh-agent`.
It reports those scopes as ineligible; inspect their recorded owner/task before
any manual action.

## Required Workflow

1. Locate the synced skill on **Hoster**. The skill and helper are colocated:

   ```bash
   REAPER="$HOME/.hermes/synced-skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py"
   test -f "$REAPER"
   ```

   If that projection is absent, do not copy a scratch script or invent a
   substitute. Report the missing projection and use the normal General Skills
   sync/deployment path.

2. When you create a new agent-owned child pane, register it immediately—while
   its pane and tmux server are live. This is the ownership receipt that makes
   later cleanup possible. From that pane:

   ```bash
   PANE_PID="$(tmux display-message -p '#{pane_pid}')"
   python3 "$REAPER" --register-pane "$PANE_PID"
   ```

   Existing legacy/unregistered scopes intentionally remain inspect-only.

3. Inspect first. Run in Hoster's user-systemd environment and save/report the
   one-line JSON receipt:

   ```bash
   export XDG_RUNTIME_DIR="/run/user/$(id -u)"
   export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
   python3 "$REAPER"
   ```

4. Review candidates. `eligible: true` means the helper has matched the narrow
   ownership proof above. Anything with `eligible: false` is **not** permission
   to stop it; `unregistered-scope` means it is deliberately legacy/ambiguous.

5. Apply only after the inspection returned at least one eligible scope:

   ```bash
   python3 "$REAPER" --apply
   ```

   The helper rechecks each exact scope immediately before stopping it and emits
   `stopped` in its JSON receipt.

6. Include the receipt summary in the parent task handoff: count inspected,
   scopes stopped, and count requiring human/owner review. Do not treat a clean
   zero-candidate receipt as a failure.

## Invocation From the Control Host

Use a short-lived SSH command only for this bounded preflight. Do not start a
new durable service merely to run the reaper:

```bash
ssh -i "${HOSTER_SSH_KEY:-$HOME/.ssh/hoster}" \
  -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T ryushe@hoster '
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
    REAPER="$HOME/.hermes/synced-skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py"
    python3 "$REAPER"
  '
```

After reviewing an eligible-only receipt, repeat the command with `--apply`.

## Do Not

- Do not schedule this as a timer, cron job, or unattended background loop.
- Do not mass-kill `tmux`, Chromium, `ssh-agent`, VNC, or user scopes.
- Do not equate an old process with an orphaned agent task.
- Do not delete panes or restart `hoster-ghost-workspace.service` as cleanup.
- Do not run `--apply` when the workspace socket cannot be inspected.

## Verification

- [ ] The helper is executed from the synced `hoster-tmux-child-reaper` skill,
      not from a per-host scratch directory.
- [ ] The inspect receipt was reviewed before any `--apply` call.
- [ ] Every stopped scope appears in the `stopped` array of the apply receipt.
- [ ] Ineligible scopes were only reported, not stopped.
