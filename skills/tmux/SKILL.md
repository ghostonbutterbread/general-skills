---
name: tmux
description: Use when starting, supervising, checking, attaching to, or cleaning up long-running terminal sessions such as Arjun, fuzzing, recon, subdomain enumeration, scanners, SSH tasks, or interactive CLIs that should persist beyond the current agent turn.
---

# Tmux Long-Running Session Protocol

Use this skill for long-running work that should remain inspectable and
attachable instead of being tied to one Codex/OpenClaw tool call.

Use normal shell commands for quick, bounded commands. Use tmux when a command
may run for minutes or hours, needs periodic check-ins, or Ryushe may want to
attach and watch it directly.

## Core Rule

Do not kill long-running recon, fuzzing, Arjun, subdomain, crawler, scanner, or
SSH work just because the current turn is ending. Put local work in a named tmux
session, log it to disk, record a manifest, and report how to attach/check/stop
it.

**Hoster exception:** never start bare tmux, `nohup`, `setsid`, or `&` through
an SSH login to Hoster. Load `hoster-ssh` and dispatch the tmux session inside
its named `systemd-run --user` service; a detached tmux session does not escape
`ssh.service` by itself.

## Session Registry

All Ghost-created long-running tmux sessions must have a manifest under:

```text
/home/ryushe/.tmux_sessions/
```

Use one JSON file per session:

```text
/home/ryushe/.tmux_sessions/<session-name>.json
```

Manifest fields:

- `session`: tmux session name
- `created_at`: UTC ISO timestamp
- `program`: target/program slug when relevant
- `purpose`: short human-readable goal
- `command`: exact command launched
- `cwd`: working directory
- `log_file`: stdout/stderr log path
- `artifact_dir`: primary output directory
- `rate_limit`: declared request rate or `local/no-network`
- `input`: input file/path/URL
- `status`: `running`, `completed`, `stopped`, or `unknown`
- `check_command`: exact tmux capture command
- `attach_command`: exact tmux attach command
- `stop_command`: exact tmux kill-session command

Never put cookies, bearer tokens, API keys, passwords, private config values, or
other secrets in the manifest. Put secret-bearing runtime data only in the
approved target artifact location with restricted permissions.

## Naming

Use predictable names:

```text
<program>-<task>-<YYYYMMDDTHHMMSSZ>
```

Examples:

- `superdrug-arjun-20260618T020000Z`
- `canva-subfinder-20260618T020000Z`
- `opera-air-ffuf-20260618T020000Z`

Keep names lowercase and shell-safe: letters, numbers, dash, underscore.

## Start Pattern

Resolve storage with `/bounty-storage` first. Long-running bounty output should
default to `/mnt/bounty`; keep only compact manifests, pointers, and curated
promotions in Shared.

Create an artifact directory first, then start tmux detached:

```bash
run_id="$(date -u +%Y%m%dT%H%M%SZ)"
session="superdrug-arjun-$run_id"
artifact_dir="/mnt/bounty/superdrug/web/recon/fuzzing/arjun/runs/$run_id"
shared_manifest_dir="/home/ryushe/Shared/web_bounty/superdrug/web/recon/fuzzing/arjun"
mkdir -p "$artifact_dir" "$shared_manifest_dir" /home/ryushe/.tmux_sessions

tmux new-session -d -s "$session" -c /home/ryushe/projects/bug_bounty_harness \
  "arjun -i '$artifact_dir/input_urls.txt' --rate-limit 2 -t 2 -d 0.5 -T 10 --disable-redirects --stable -o '$artifact_dir/arjun.json' -oT '$artifact_dir/arjun.txt' 2>&1 | tee -a '$artifact_dir/run.log'; printf '\n[tmux-run-complete] %s\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" | tee -a '$artifact_dir/run.log'"
```

Then write the manifest:

```bash
cat > "/home/ryushe/.tmux_sessions/$session.json" <<EOF
{
  "session": "$session",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "program": "superdrug",
  "purpose": "Arjun hidden parameter discovery",
  "command": "arjun ...",
  "cwd": "/home/ryushe/projects/bug_bounty_harness",
  "log_file": "$artifact_dir/run.log",
  "artifact_dir": "$artifact_dir",
  "rate_limit": "2 req/sec, 2 threads, 0.5s delay, 10s timeout",
  "input": "$artifact_dir/input_urls.txt",
  "status": "running",
  "check_command": "tmux capture-pane -t $session -p -S - | tail -80",
  "attach_command": "tmux attach -t $session",
  "stop_command": "tmux kill-session -t $session"
}
EOF
```

Then write a compact Shared run pointer, not raw tool output:

```bash
cat > "$shared_manifest_dir/$run_id.manifest.json" <<EOF
{
  "run_id": "$run_id",
  "program": "superdrug",
  "tool_or_skill": "tmux/arjun",
  "status": "running",
  "heavy_artifact_root": "$artifact_dir",
  "tmux_manifest": "/home/ryushe/.tmux_sessions/$session.json",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "curated_shared_outputs": []
}
EOF
```

If using shell quoting would make the manifest error-prone, write it with a
small one-shot Python snippet. Do not include secrets.

## Check Pattern

Check a session without attaching:

```bash
tmux has-session -t superdrug-arjun-20260618T020000Z
tmux capture-pane -t superdrug-arjun-20260618T020000Z -p -S - | tail -80
tail -80 /path/to/artifact/run.log
```

Update the manifest status when a run completes, is stopped, or is found dead.

## Attach Pattern

Tell Ryushe:

```bash
tmux attach -t superdrug-arjun-20260618T020000Z
```

Detach without stopping the command:

```text
Ctrl-b then d
```

## Stop Pattern

Only stop a long-running tmux session when one of these is true:

- Ryushe asks to stop it.
- The command is clearly unsafe, out-of-scope, runaway, or violating rate limits.
- The task has completed and the pane is idle.
- You are replacing it with a better-scoped session and you report why.

Stop command:

```bash
tmux kill-session -t superdrug-arjun-20260618T020000Z
```

Record the reason in the manifest or a run note.

## Agent Reporting

When starting a long-running tmux session, always report:

- session name
- tool/command
- input file or URL set
- rate limit / threads / timeout
- artifact directory
- log file
- attach command
- check command
- whether it is live traffic or local/no-network

When checking a session, report:

- still running or completed
- latest visible output summary
- output files created or updated
- errors/prompts needing attention
- next check suggestion

## Common Commands

```bash
tmux ls
tmux new-session -d -s name
tmux attach -t name
tmux capture-pane -t name -p
tmux capture-pane -t name -p -S -
tmux send-keys -t name C-c
tmux kill-session -t name
```

Target format can include window/pane:

```text
session:window.pane
```

Example:

```bash
tmux capture-pane -t shared:0.0 -p -S -
```

## Long-Running Runner Defaults

Use tmux by default for:

- Arjun or parameter mining over more than a tiny smoke set
- ffuf/fuzzing runs over large wordlists
- subdomain enumeration
- passive recon collectors
- JS crawling or browser crawling that may run longer than a few minutes
- interactive CLIs on the local machine
- SSH work on non-Hoster machines where tmux is the declared remote supervisor
- anything Ryushe may want to attach to directly

For any durable workload on Hoster, use `hoster-ssh` instead; it launches a
named tmux session only inside a Hoster user-systemd service.

Prefer direct shell execution only for:

- short version checks
- file inspection
- small local transforms
- focused unit tests
- tiny smoke runs that finish quickly

## Safety

Long-running does not mean unbounded. Always set:

- explicit scope/input
- rate limit or delay for live traffic
- output/log paths
- stop condition when known
- periodic check plan when useful

If scope or rate is unknown, ask or run local/no-network preparation first.
