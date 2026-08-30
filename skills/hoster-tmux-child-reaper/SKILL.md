---
name: hoster-tmux-child-reaper
description: Use when starting meaningful Hoster work to run a short-lived cleanup sidecar that safely reconciles completed agent-created tmux scopes.
---

# Hoster Cleanup Sidecar

When an agent begins meaningful work on Hoster, it starts a **small, short-lived
cleanup sidecar** and immediately proceeds with its own task. The sidecar owns
Hoster tmux-scope hygiene; the main worker does not need to inspect scopes,
create a tmux pane, or interpret low-level cleanup details.

This is an explicit entry workflow, **never** a timer, cron job, or background
loop. Load `hoster-ssh` first for the Hoster connection and user-systemd
environment. This skill does not replace `hoster-workspace`, the durable
`ghost-workspace`, or normal task cleanup.

## Parent Contract

1. Start one bounded native subagent as a sidecar when Hoster work begins. It
   may run concurrently with the actual Hoster task because it only considers
   previously registered, empty scopes.
2. Give it the cleanup packet below. It runs inspect first and may apply only
   the helper's already-narrow eligibility rule.
3. Continue the main task. Do not block normal work waiting for a routine
   cleanup receipt.
4. When the sidecar returns, preserve its compact status in the task handoff.
   A `needs-attention` result is context for the parent, not permission for the
   parent to mass-kill or restart anything.

The sidecar is an agent role, not a tmux child pane. “tmux child pane” is only
an existing low-level systemd scope description used by the helper.

## Cleanup Sidecar Packet

```text
Objective: Reconcile Hoster tmux-spawn scope residue **while the parent begins**
its Hoster task; do not delay the parent.

Scope: Run only the synced hoster-tmux-child-reaper helper through bounded SSH.
Inspect first; run --apply only if the inspection receipt contains eligible
scopes. Return one compact status receipt to the parent.

Out of scope: Parent task implementation; creating panes; restarting
hoster-ghost-workspace; killing tmux, browsers, VNC, proxies, scanners, agents,
ssh-agent, or arbitrary user scopes; timers/cron; manual remediation of
ineligible scopes.

Stop condition: The inspect/apply receipt is produced, or a missing projection,
SSH/user-systemd failure, or unsafe/ambiguous state is identified.

Required output:
- cleanup: success | needs-attention | failed
- inspected: <count>
- stopped: <count>
- retained: <count>
- reason: one short sentence
- receipt: <sanitized path or JSON summary>
```

Use `success` for a completed inspection/apply where no unsafe condition or
execution failure occurred, including a clean zero-stop result. Use
`needs-attention` when protected or ambiguous residue was retained. Use
`failed` only when the sidecar could not run or verify its bounded workflow.

## Boundaries

The bundled helper considers a scope eligible only when all conditions hold:

1. it was explicitly registered while its live pane and tmux-server identity
   were verified;
2. systemd's current description and cgroup still exactly match that immutable
   registration record; and
3. the scope contains **no processes at all**.

A residual `ssh-agent` is reported but not stopped: a pane might be on an
arbitrary local tmux socket that cannot be fully inventoried. The helper never
selects ordinary tmux panes by age or name, and never stops a scope with any
remaining process, including Claude, Codex, Chromium, VNC, proxy, scanner, or
`ssh-agent`. Ineligible scopes are reported only.

## Sidecar Procedure

1. Locate the synced helper on **Hoster**. The skill and executable are
   colocated:

   ```bash
   REAPER="$HOME/.hermes/synced-skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py"
   test -f "$REAPER"
   ```

   If this projection is absent, do not copy a scratch script or invent a
   substitute. Return `cleanup: failed` and report the missing projection.

2. Run the inspect-only command in Hoster's user-systemd environment and retain
   its JSON receipt:

   ```bash
   export XDG_RUNTIME_DIR="/run/user/$(id -u)"
   export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
   python3 "$REAPER"
   ```

3. If and only if the receipt contains one or more `eligible: true` scopes, run
   `python3 "$REAPER" --apply`. The helper rechecks each exact scope immediately
   before stopping it and emits `stopped` in its JSON receipt.

4. Return the compact sidecar status. Do not manually act on ineligible scopes.

## Registration Is a Separate Launcher Concern

The helper can clean only scopes that were registered at their own verified
creation boundary. Existing legacy/unregistered scopes deliberately remain
inspect-only. The main Hoster worker must not be burdened with a manual
registration ritual; if a future Hoster pane/agent launcher needs reaping
coverage, that launcher must register its own proven scope as part of creation.
Do not have the cleanup sidecar retrospectively claim arbitrary active scopes.

## Invocation From the Control Host

The sidecar uses a short-lived SSH command only for this bounded reconciliation:

```bash
ssh -i "${HOSTER_SSH_KEY:-$HOME/.ssh/hoster}" \
  -o BatchMode=yes -o ConnectTimeout=10 -o ControlMaster=no -T ryushe@hoster '
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
    REAPER="$HOME/.hermes/synced-skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py"
    python3 "$REAPER"
  '
```

## Do Not

- Do not schedule cleanup as a timer, cron job, or unattended loop.
- Do not make the main worker wait for normal cleanup before beginning its task.
- Do not create a tmux pane just to run this sidecar.
- Do not mass-kill `tmux`, Chromium, `ssh-agent`, VNC, or user scopes.
- Do not equate an old process with an orphaned agent task.
- Do not delete panes or restart `hoster-ghost-workspace.service` as cleanup.
- Do not run `--apply` without an immediately preceding inspected receipt.

## Verification

- [ ] The sidecar executed the synced helper, not a per-host scratch copy.
- [ ] The sidecar inspected before any `--apply` action.
- [ ] Every stopped scope appears in the apply receipt's `stopped` array.
- [ ] Ineligible scopes were reported, not stopped.
- [ ] The parent received the compact cleanup status.
